import argparse
import pathlib
import sys

from concurrent.futures import ThreadPoolExecutor
from os import cpu_count

from tools import TOOLS
from tool import basename, execute


def run_tool(tool, timed_out, patterns, reads, **params):
    if not timed_out[tool.name]:
        time = tool.run(patterns, reads, **params)
        timed_out[tool.name] |= time == float("inf")


def run(args):
    reads = pathlib.Path(args.reads)
    reads_name = basename(reads)
    assert reads.exists()
    patterns_dir = pathlib.Path(args.patterns_dir)
    patterns_dir.mkdir(exist_ok=True)
    log_dir = pathlib.Path(args.log_dir)
    log_dir.mkdir(exist_ok=True)
    k = args.kmer_size
    m = args.minimizer_size

    selected_tool_names = [name.lower() for name in args.select_tools]
    excluded_tool_names = [name.lower() for name in args.exclude_tools]
    selected_tools = [
        tool
        for tool in TOOLS
        if tool.name.lower() in selected_tool_names
        and tool.name.lower() not in excluded_tool_names
    ]
    selected_tool_names = [tool.name for tool in selected_tools]

    ref_timed_out = {name: False for name in selected_tool_names}
    random_timed_out = {name: False for name in selected_tool_names}
    max_workers = max(args.max_workers // args.threads, 1)
    for n in args.num_patterns:
        random_fasta = patterns_dir / f"random_{n}.fa"
        random_txt = random_fasta.with_suffix(".txt")
        ref_fasta = patterns_dir / f"{reads_name}_{n}.fa"
        ref_txt = ref_fasta.with_suffix(".txt")
        ref_fasta_matchtigs = patterns_dir / f"{reads_name}_matchtigs_{n}.fa"
        execute(
            f"pattern_extract -k {k} -n {n} -f {random_fasta} -t {random_txt}",
            silent=True,
        )
        execute(
            f"pattern_extract -k {k} -n {n} -r {reads} -f {ref_fasta} -t {ref_txt}",
            silent=True,
        )
        if args.matchtigs and not ref_fasta_matchtigs.exists():
            execute(
                f"ggcat build -k {k} -s 1 -f -j {args.max_workers} -m 8 -p --greedy-matchtigs -o {ref_fasta_matchtigs} {ref_fasta}",
                silent=True,
            )
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for n in args.num_patterns:
            random_fasta = patterns_dir / f"random_{n}.fa"
            random_txt = random_fasta.with_suffix(".txt")
            ref_fasta = patterns_dir / f"{reads_name}_{n}.fa"
            ref_txt = ref_fasta.with_suffix(".txt")
            if args.matchtigs:
                ref_fasta = patterns_dir / f"{reads_name}_matchtigs_{n}.fa"
            for tool in selected_tools:
                if max_workers > 1:
                    futures.append(
                        executor.submit(
                            run_tool,
                            tool,
                            random_timed_out,
                            random_fasta,
                            reads,
                            repeat=args.repeat,
                            timeout=args.timeout,
                            overwrite_log=args.overwrite_logs,
                            log_dir=log_dir,
                            num_patterns=n,
                            random=True,
                            matchtigs=False,
                            threads=args.threads,
                            threshold=args.threshold,
                            k=k,
                            m=m,
                            silent=True,
                        )
                    )
                else:
                    run_tool(
                        tool,
                        random_timed_out,
                        random_fasta,
                        reads,
                        repeat=args.repeat,
                        timeout=args.timeout,
                        overwrite_log=args.overwrite_logs,
                        log_dir=log_dir,
                        num_patterns=n,
                        random=True,
                        matchtigs=False,
                        threads=args.threads,
                        threshold=args.threshold,
                        k=k,
                        m=m,
                    )
            for tool in selected_tools:
                if max_workers > 1:
                    futures.append(
                        executor.submit(
                            run_tool,
                            tool,
                            ref_timed_out,
                            ref_fasta,
                            reads,
                            repeat=args.repeat,
                            timeout=args.timeout,
                            overwrite_log=args.overwrite_logs,
                            log_dir=log_dir,
                            num_patterns=n,
                            random=False,
                            matchtigs=args.matchtigs,
                            threads=args.threads,
                            threshold=args.threshold,
                            k=k,
                            m=m,
                            silent=True,
                        )
                    )
                else:
                    run_tool(
                        tool,
                        ref_timed_out,
                        ref_fasta,
                        reads,
                        repeat=args.repeat,
                        timeout=args.timeout,
                        overwrite_log=args.overwrite_logs,
                        log_dir=log_dir,
                        num_patterns=n,
                        random=False,
                        matchtigs=args.matchtigs,
                        threads=args.threads,
                        threshold=args.threshold,
                        k=k,
                        m=m,
                    )
        for future in futures:
            future.result()


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
        default=[2**p for p in range(25)],
    )
    parser.add_argument(
        "-s",
        "--select_tools",
        help="select tools to run [all]",
        nargs="+",
        type=str,
        default=[tool.name for tool in TOOLS],
    )
    parser.add_argument(
        "-x",
        "--exclude_tools",
        help="exclude specific tools [none]",
        nargs="+",
        type=str,
        default=[],
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
        "-j",
        "--threads",
        help="number of threads for each tool [8]",
        type=int,
        default=8,
    )
    parser.add_argument(
        "-w",
        "--max_workers",
        help="total number of workers shared between all tools",
        type=int,
        default=cpu_count() // 2,
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
        "-M",
        "--matchtigs",
        help="compute matchtigs from patterns [False]",
        type=bool,
        default=False,
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
