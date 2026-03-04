use clap::Parser as ClapParser;
use helicase::input::*;
use helicase::*;
use nohash_hasher::BuildNoHashHasher;

use packed_seq::{AsciiSeqVec, SeqVec};
use seq_hash::{KmerHasher, NtHasher, packed_seq};

use std::collections::HashSet;
use std::fs::{File, exists};
use std::io::{BufWriter, Write};

const CONFIG: Config = ParserOptions::default()
    .ignore_headers()
    .dna_packed()
    .and_dna_string()
    .config();

#[derive(ClapParser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Reference to extract k-mers from (random by default)
    #[arg(short, long)]
    reference: Option<String>,
    /// K-mer size
    #[arg(short, default_value_t = 31)]
    k: usize,
    /// Number of k-mers to extract
    #[arg(short, long)]
    num_kmers: usize,
    /// Path to the fasta output
    #[arg(short, long)]
    fasta: Option<String>,
    /// Path to the text output (one line per k-mer)
    #[arg(short, long)]
    text: Option<String>,
}

fn main() {
    let args = Args::parse();

    let mut fasta_writer = if let Some(fasta_path) = args.fasta
        && !exists(&fasta_path).expect("Cannot check output path")
    {
        let fasta_file = File::create_new(&fasta_path).expect("Cannot create output file");
        Some(BufWriter::new(fasta_file))
    } else {
        None
    };

    let mut text_writer = if let Some(text_path) = args.text
        && !exists(&text_path).expect("Cannot check output path")
    {
        let text_file = File::create_new(&text_path).expect("Cannot create output file");
        Some(BufWriter::new(text_file))
    } else {
        None
    };

    if fasta_writer.is_none() && text_writer.is_none() {
        eprintln!("No new output specified");
        return;
    }

    if let Some(reference_path) = args.reference {
        let mut parser =
            FastxParser::<CONFIG>::from_file(&reference_path).expect("Cannot open reference file");

        let hasher = NtHasher::<false>::new(args.k);
        let mut hashes = Vec::with_capacity(1 << 15);
        let mut seen =
            HashSet::with_capacity_and_hasher(args.num_kmers * 2, BuildNoHashHasher::<u64>::new());

        while let Some(_) = parser.next() {
            let seq = parser.get_dna_string();
            let packed = parser.get_packed_seq();
            if seq.len() < args.k {
                continue;
            }

            hashes.clear();
            hasher.hash_kmers_simd(packed, 1).collect_into(&mut hashes);

            let mut stop = args.k - 1;
            for (kmer, &hash) in seq.windows(args.k).zip(hashes.iter()) {
                stop += 1;
                if seen.insert(hash) {
                    if let Some(ref mut writer) = text_writer {
                        writer.write_all(kmer).unwrap();
                        writer.write_all(b"\n").unwrap();
                    }
                    if seen.len() == args.num_kmers {
                        break;
                    }
                }
            }
            if let Some(ref mut writer) = fasta_writer {
                writer.write_all(b">\n").unwrap();
                writer.write_all(&seq[..stop]).unwrap();
                writer.write_all(b"\n").unwrap();
            }
            if seen.len() == args.num_kmers {
                break;
            }
        }
    } else {
        let seq = AsciiSeqVec::random(args.num_kmers + args.k - 1).into_raw();
        for kmer in seq.windows(args.k) {
            if let Some(ref mut writer) = text_writer {
                writer.write_all(kmer).unwrap();
                writer.write_all(b"\n").unwrap();
            }
        }
        if let Some(ref mut writer) = fasta_writer {
            writer.write_all(b">\n").unwrap();
            writer.write_all(&seq).unwrap();
            writer.write_all(b"\n").unwrap();
        }
    }
}
