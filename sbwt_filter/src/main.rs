use clap::Parser as ClapParser;
use needletail::parse_fastx_file;
use sbwt::{BitPackedKmerSortingMem, SbwtIndexBuilder, StreamingIndex};

use std::fs::File;
use std::path::PathBuf;
use std::time::Instant;

#[derive(ClapParser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Read FASTA/Q file
    #[arg()]
    reads: PathBuf,
    /// Pattern FASTA file
    #[arg(short, long)]
    patterns: PathBuf,
    /// K-mer size
    #[arg(short, long, default_value_t = 31)]
    k: usize,
    /// Number of threads used for index construction
    #[arg(short, long, default_value_t = 8)]
    threads: usize,
    /// Approximate memory budget for SBWT construction
    #[arg(long, default_value_t = 8)]
    mem_gb: usize,
}

fn main() {
    let args = Args::parse();
    let pattern_file = File::open(&args.patterns).expect("Cannot open patterns file");

    let start = Instant::now();
    let (sbwt, lcs) = SbwtIndexBuilder::<BitPackedKmerSortingMem>::new()
        .k(args.k)
        .n_threads(args.threads.max(1))
        .build_lcs(true)
        .algorithm(BitPackedKmerSortingMem::new().mem_gb(args.mem_gb))
        .run_from_fasta(pattern_file);
    let lcs = lcs.expect("SBWT LCS array was not constructed");
    let streaming_index = StreamingIndex::new(&sbwt, &lcs);
    eprintln!("Indexing took {:.02} s", start.elapsed().as_secs_f64());

    let mut reader = parse_fastx_file(&args.reads).expect("Failed to parse reads");
    let start = Instant::now();
    let mut checksum: u64 = 0;
    while let Some(record) = reader.next() {
        let record = record.unwrap();
        let seq = &record.seq();
        for (len, range) in streaming_index.matching_statistics(seq) {
            checksum = checksum
                .wrapping_add(len as u64)
                .wrapping_add(range.start as u64)
                .wrapping_add(range.end as u64);
        }
    }
    eprintln!("Filtering took {:.02} s", start.elapsed().as_secs_f64());
}
