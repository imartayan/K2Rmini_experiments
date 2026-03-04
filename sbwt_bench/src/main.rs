use clap::Parser as ClapParser;
use needletail::Sequence;
use sbwt::{BitPackedKmerSortingMem, SbwtIndexBuilder, StreamingIndex};

use std::error::Error;
use std::fs::File;
use std::path::PathBuf;

#[derive(ClapParser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// K-mer size
    #[arg(short, long, default_value_t = 31)]
    k: usize,
    /// Pattern FASTA file
    #[arg(short, long)]
    patterns: PathBuf,
    /// Read FASTA/Q file
    #[arg(short, long)]
    reads: PathBuf,
    /// Number of threads used for index construction
    #[arg(short, long, default_value_t = 8)]
    threads: usize,
    /// Approximate memory budget for SBWT construction
    #[arg(long, default_value_t = 8)]
    mem_gb: usize,
}

fn main() -> Result<(), Box<dyn Error>> {
    let args = Args::parse();
    let pattern_file = File::open(&args.patterns)?;

    let (sbwt, lcs) = SbwtIndexBuilder::<BitPackedKmerSortingMem>::new()
        .k(args.k)
        .n_threads(args.threads.max(1))
        .build_lcs(true)
        .algorithm(BitPackedKmerSortingMem::new().mem_gb(args.mem_gb))
        .run_from_fasta(pattern_file);
    let lcs = lcs.ok_or("SBWT LCS array was not constructed")?;
    let streaming_index = StreamingIndex::new(&sbwt, &lcs);

    let mut reader = needletail::parse_fastx_file(&args.reads)?;
    let mut checksum: u64 = 0;
    while let Some(record) = reader.next() {
        let record = record?;
        let normalized = record.normalize(false);
        for (len, range) in streaming_index.matching_statistics(normalized.as_ref()) {
            checksum = checksum
                .wrapping_add(len as u64)
                .wrapping_add(range.start as u64)
                .wrapping_add(range.end as u64);
        }
    }

    std::hint::black_box(checksum);
    Ok(())
}
