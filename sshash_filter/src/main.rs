use clap::Parser as ClapParser;
use crossbeam_channel::bounded;
use helicase::input::*;
use helicase::*;
use sshash_lib::{BuildConfiguration, Dictionary, DictionaryBuilder, dispatch_on_k};

use core::fmt::Display;
use core::mem::swap;
use core::str::FromStr;
use std::fs::File;
use std::io::{self, BufWriter, Write, stdout};
use std::sync::Arc;
use std::thread;
use std::time::Instant;

const MSG_LEN_THRESHOLD: usize = 8000; // small enough for long reads

const CONFIG: Config = ParserOptions::default().config();

#[derive(Debug, Clone, Copy)]
enum Threshold {
    Absolute(usize),
    Relative(f64),
}

impl FromStr for Threshold {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if let Ok(val) = s.parse::<usize>() {
            if val == 0 {
                Err("Absolute threshold must be ≥ 1".to_string())
            } else {
                Ok(Self::Absolute(val))
            }
        } else if let Ok(val) = s.parse::<f64>() {
            if val.is_nan() || val.is_sign_negative() || val == 0. || val > 1. {
                Err("Relative threshold must in (0, 1]".to_string())
            } else {
                Ok(Self::Relative(val))
            }
        } else {
            Err("Invalid threshold format, pass an int or a float".to_string())
        }
    }
}

impl Display for Threshold {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Absolute(x) => write!(f, "{x}"),
            Self::Relative(x) => write!(f, "{x}"),
        }
    }
}

#[derive(ClapParser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// FASTA/Q file to filter (possibly compressed)
    #[arg()]
    file: String,
    /// FASTA/Q file containing k-mers of interest (possibly compressed)
    #[arg(short)]
    patterns: String,
    /// K-mer threshold, either relative (float) or absolute (int)
    #[arg(short, long, default_value_t = Threshold::Relative(0.5))]
    threshold: Threshold,
    /// Output file for filtered sequences [default: stdout]
    #[arg(short)]
    output: Option<String>,
    /// K-mer size
    #[arg(short, default_value_t = 31)]
    k: usize,
    /// Minimizer size
    #[arg(short, default_value_t = 21)]
    m: usize,
    /// Number of threads [default: all]
    #[arg(short = 'T', long)]
    threads: Option<usize>,
}

// https://github.com/Daniel-Liu-c0deb0t/simple-saca/blob/main/src/main.rs#L96
fn mem_usage_gb() -> f64 {
    let rusage = unsafe {
        let mut rusage = std::mem::MaybeUninit::uninit();
        libc::getrusage(libc::RUSAGE_SELF, rusage.as_mut_ptr());
        rusage.assume_init()
    };
    let maxrss = rusage.ru_maxrss as f64;
    if cfg!(target_os = "macos") {
        maxrss / 1_000_000_000.
    } else {
        maxrss / 1_000_000.
    }
}

fn main() -> io::Result<()> {
    let args = Args::parse();
    assert!(args.m <= args.k, "Minimizer size must be ≤ k");
    eprintln!(
        "Running with k={} and {} threshold of {}",
        args.k,
        match args.threshold {
            Threshold::Absolute(_) => "an absolute",
            Threshold::Relative(_) => "a relative",
        },
        args.threshold
    );

    eprintln!("Building SSHash on patterns...");
    let start = Instant::now();
    let dict = index_reference(&args);
    eprintln!(
        "Took {:.02} s, RAM: {:.03} GB",
        start.elapsed().as_secs_f64(),
        mem_usage_gb()
    );
    let dict = Arc::new(dict);

    eprintln!("Filtering sequences in parallel...");
    let start = Instant::now();
    process_query_streaming(&args, Arc::clone(&dict))?;
    eprintln!(
        "Took {:.02} s, RAM: {:.03} GB",
        start.elapsed().as_secs_f64(),
        mem_usage_gb()
    );

    Ok(())
}

fn index_reference(args: &Args) -> Dictionary {
    let threads = args.threads.unwrap_or_else(|| {
        thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(4)
    });
    let mut parser =
        FastxParser::<CONFIG>::from_file_in_ram(&args.patterns).expect("Cannot open file");
    let mut sequences = Vec::new();
    while let Some(_event) = parser.next() {
        sequences.push(String::from_utf8(parser.get_dna_string_owned()).unwrap());
    }
    let mut config = BuildConfiguration::new(args.k, args.m).unwrap();
    config.num_threads = threads;
    let builder = DictionaryBuilder::new(config).unwrap();
    builder.build_from_sequences(sequences).unwrap()
}

fn process_query_streaming(args: &Args, dict: Arc<Dictionary>) -> io::Result<()> {
    let kmer_size: usize = args.k;
    let threshold = args.threshold;
    let output = args.output.clone();
    let num_consumers = args.threads.unwrap_or_else(|| {
        thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(4)
    });

    let path = args.file.clone();
    let (record_tx, record_rx) = bounded(2 * num_consumers);
    let (result_tx, result_rx) = bounded(4 * num_consumers);

    let producer_handle = thread::spawn(move || {
        let mut ids = Vec::new();
        let mut seqs = Vec::new();
        let mut ends = Vec::new();
        let mut parser =
            FastxParser::<CONFIG>::from_file(&path).expect("Failed to parse file to filter");
        while let Some(_) = parser.next() {
            let id = parser.get_header();
            let seq = parser.get_dna_string();
            if seq.len() < kmer_size {
                continue;
            }
            ids.extend_from_slice(id);
            seqs.extend_from_slice(seq);
            ends.push((ids.len(), seqs.len()));
            if seqs.len() >= MSG_LEN_THRESHOLD {
                let mut tmp_ids = Vec::new();
                let mut tmp_seqs = Vec::new();
                let mut tmp_ends = Vec::new();
                swap(&mut ids, &mut tmp_ids);
                swap(&mut seqs, &mut tmp_seqs);
                swap(&mut ends, &mut tmp_ends);
                if record_tx.send((tmp_ids, tmp_seqs, tmp_ends)).is_err() {
                    break;
                }
            }
        }
        if !seqs.is_empty() {
            record_tx.send((ids, seqs, ends)).unwrap();
        }
    });

    let mut consumer_handles = Vec::with_capacity(num_consumers);
    dispatch_on_k!(kmer_size, K => {
    for _ in 0..num_consumers {
        let record_rx_clone = record_rx.clone();
        let result_tx_clone = result_tx.clone();
        let dict_clone = Arc::clone(&dict);

        let handle = thread::spawn(move || {
                        let mut streaming = dict_clone.create_streaming_query::<K>();
                        while let Ok((ids, seqs, ends)) = record_rx_clone.recv() {
                            if ends.len() == 1 {
                                // a single long seq
                                let id = &ids;
                                let seq = &seqs;

                                let kmer_threshold: usize = match threshold {
                                    Threshold::Absolute(n) => n,
                                    Threshold::Relative(f) => {
                                        (((seq.len().saturating_sub(kmer_size) + 1) as f64) * f).ceil() as usize
                                    }
                                };

                                streaming.reset();
                                let kmer_match_count = seq
                                    .windows(kmer_size)
                                    .filter(|&kmer| streaming.lookup(kmer).is_found())
                                    .count();
                                if kmer_match_count >= kmer_threshold {
                                    let _ = result_tx_clone.send((id.clone(), seq.clone()));
                                    break;
                                }
                            } else {
                                // multiple short seqs
                                let mut id_start = 0;
                                let mut seq_start = 0;
                                for (id_end, seq_end) in ends.iter().copied() {
                                    let id = &ids[id_start..id_end];
                                    let seq = &seqs[seq_start..seq_end];

                                    let kmer_threshold: usize = match threshold {
                                        Threshold::Absolute(n) => n,
                                        Threshold::Relative(f) => {
                                            (((seq.len().saturating_sub(kmer_size) + 1) as f64) * f).ceil()
                                                as usize
                                        }
                                    };

                                    streaming.reset();
                                    let kmer_match_count = seq
                                        .windows(kmer_size)
                                        .filter(|&kmer| streaming.lookup(kmer).is_found())
                                        .count();
                                    if kmer_match_count >= kmer_threshold {
                                        let _ = result_tx_clone.send((id.to_vec(), seq.to_vec()));
                                        break;
                                    }

                                    id_start = id_end;
                                    seq_start = seq_end;
                                }
                            }
                        }

        });

        consumer_handles.push(handle);
    }
    });

    drop(result_tx);

    let printer_handle = thread::spawn(move || {
        if let Some(out) = output {
            let file = File::create(out).expect("Failed to open output file");
            let mut writer = BufWriter::new(file);
            for (id, seq) in result_rx.iter() {
                writer.write_all(b">")?;
                writer.write_all(&id)?;
                writer.write_all(b"\n")?;
                writer.write_all(&seq)?;
                writer.write_all(b"\n")?;
            }
        } else {
            for (id, seq) in result_rx.iter() {
                stdout().write_all(b">")?;
                stdout().write_all(&id)?;
                stdout().write_all(b"\n")?;
                stdout().write_all(&seq)?;
                stdout().write_all(b"\n")?;
            }
        }
        io::Result::Ok(())
    });

    producer_handle.join().expect("Producer thread panicked");
    for handle in consumer_handles {
        handle.join().expect("Consumer thread panicked");
    }
    let _ = printer_handle.join().expect("Printer thread panicked");

    Ok(())
}
