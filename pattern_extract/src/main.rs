use clap::Parser as ClapParser;
use gxhash::GxBuildHasher;
use helicase::input::*;
use helicase::*;
use nohash_hasher::BuildNoHashHasher;
use packed_seq::{AsciiSeqVec, SeqVec};

use std::collections::HashSet;
use std::fs::{File, exists};
use std::hash::BuildHasher;
use std::io::{BufWriter, Write};

const CONFIG: Config = ParserOptions::default().ignore_headers().config();

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
    /// Path to the fasta output (one record per k-mer)
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

        let hasher = GxBuildHasher::default();
        let mut seen =
            HashSet::with_capacity_and_hasher(args.num_kmers * 2, BuildNoHashHasher::<u64>::new());

        while let Some(_) = parser.next() {
            let seq = parser.get_dna_string();
            for kmer in seq.windows(args.k) {
                let hash = hasher.hash_one(kmer);
                if seen.insert(hash) {
                    if let Some(ref mut writer) = fasta_writer {
                        writer.write_all(b">\n").unwrap();
                        writer.write_all(kmer).unwrap();
                        writer.write_all(b"\n").unwrap();
                    }
                    if let Some(ref mut writer) = text_writer {
                        writer.write_all(kmer).unwrap();
                        writer.write_all(b"\n").unwrap();
                    }
                    if seen.len() == args.num_kmers {
                        return;
                    }
                }
            }
        }
    } else {
        let seq = AsciiSeqVec::random(args.num_kmers + args.k - 1).into_raw();
        for kmer in seq.windows(args.k) {
            if let Some(ref mut writer) = fasta_writer {
                writer.write_all(b">\n").unwrap();
                writer.write_all(kmer).unwrap();
                writer.write_all(b"\n").unwrap();
            }
            if let Some(ref mut writer) = text_writer {
                writer.write_all(kmer).unwrap();
                writer.write_all(b"\n").unwrap();
            }
        }
    }
}
