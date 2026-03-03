import argparse
import pathlib

from tools import TOOLS
from tool import basename, execute


def run(args):
    reads = pathlib.Path(args.reads)
    assert reads.exists()
    patterns_dir = pathlib.Path(args.patterns_dir)
    patterns_dir.mkdir(exist_ok=True)
    log_dir = pathlib.Path(args.log_dir)
    log_dir.mkdir(exist_ok=True)
    k = args.kmer_size
    m = args.minimizer_size

    timeout = {tool.name: False for tool in TOOLS}
    for n in args.num_patterns:
        ref_fasta = patterns_dir / f"{basename(reads)}_{n}.fa"
        ref_txt = ref_fasta.with_suffix(".txt")
        random_fasta = patterns_dir / f"random_{n}.fa"
        random_txt = random_fasta.with_suffix(".txt")
        execute(
            f"pattern_extract -k {k} -n {n} -r {reads} -f {ref_fasta} -t {ref_txt}",
            silent=True,
        )
        execute(
            f"pattern_extract -k {k} -n {n} -r {reads} -f {random_fasta} -t {random_txt}",
            silent=True,
        )
        for tool in TOOLS:
            if not timeout[tool.name]:
                time = tool.run(
                    ref_fasta,
                    reads,
                    repeat=args.repeat,
                    timeout=args.timeout,
                    overwrite_log=args.overwrite_logs,
                    log_dir=log_dir,
                    num_patterns=n,
                    random=False,
                    threads=args.threads,
                    threshold=args.threshold,
                    k=k,
                    m=m,
                )
                timeout[tool.name] |= time == float("inf")
                print()
            if not timeout[tool.name]:
                time = tool.run(
                    random_fasta,
                    reads,
                    repeat=args.repeat,
                    timeout=args.timeout,
                    overwrite_log=args.overwrite_logs,
                    log_dir=log_dir,
                    num_patterns=n,
                    random=True,
                    threads=args.threads,
                    threshold=args.threshold,
                    k=k,
                    m=m,
                )
                timeout[tool.name] |= time == float("inf")
                print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r",
        "--reads",
        help="FASTA/Q reads to filter",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-n",
        "--num_patterns",
        help="number of patterns to run with [powers of 2]",
        nargs="+",
        type=int,
        default=[2**p for p in range(23)],
    )
    parser.add_argument(
        "-R",
        "--repeat",
        help="number of repetitions [1]",
        type=int,
        default=1,
    )
    parser.add_argument(
        "-T",
        "--timeout",
        help="timeout for each tool (in s) [None]",
        type=float,
        default=None,
    )
    parser.add_argument(
        "-f",
        "--overwrite_logs",
        help="overwrite existing logs [False]",
        type=bool,
        default=False,
    )
    parser.add_argument(
        "-j", "--threads", help="number of threads [8]", type=int, default=8
    )
    parser.add_argument(
        "-t",
        "--threshold",
        help="pattern threshold (absolute or relative) [0.8]",
        type=float,
        default=0.8,
    )
    parser.add_argument(
        "-k",
        "--kmer_size",
        help="k-mer size [31]",
        type=int,
        default=31,
    )
    parser.add_argument(
        "-m",
        "--minimizer_size",
        help="minimizer size [21]",
        type=int,
        default=21,
    )
    parser.add_argument(
        "-l",
        "--log_dir",
        help="log directory ['log']",
        type=str,
        default="log",
    )
    parser.add_argument(
        "-p",
        "--patterns_dir",
        help="pattern directory ['patterns']",
        type=str,
        default="patterns",
    )
    args = parser.parse_args()
    run(args)
