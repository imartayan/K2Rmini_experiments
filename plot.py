import argparse
import itertools
import json
import pathlib

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from tools import TOOLS
from tool import basename

TOOL_NAMES = [tool.name for tool in TOOLS]
# https://github.com/ngregorich/plot_color_palettes/blob/main/README.md
PALETTE = {
    k: v
    for k, v in zip(
        TOOL_NAMES,
        [
            "#E15759",
            "#F28E2B",
            "#EDC948",
            "#9C755F",
            "#59A14F",
            "#76B7B2",
            "#B07AA1",
            "#4B4E6D",
            "#BAB0AC",
            "#FF9DA7",
            "#4E79A7",
        ],
    )
}

parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    "--format",
    help="plot format ['pdf']",
    nargs="+",
    type=str,
    default=["pdf"],
)
parser.add_argument(
    "-v",
    "--versus",
    help="parameter to plot against ['num_patterns']",
    type=str,
    default="num_patterns",
)
parser.add_argument(
    "-s",
    "--select_tools",
    help="select tools to plot [all]",
    nargs="+",
    type=str,
    default=TOOL_NAMES,
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
    "-l",
    "--log_dir",
    help="log directory ['log']",
    type=str,
    default="log",
)
parser.add_argument(
    "-p",
    "--plots_dir",
    help="plot directory ['plots']",
    type=str,
    default="plots",
)

args = parser.parse_args()
log_dir = pathlib.Path(args.log_dir)
plots_dir = pathlib.Path(args.plots_dir)
plots_dir.mkdir(exist_ok=True)

selected_tool_names = [name.lower() for name in args.select_tools]
excluded_tool_names = [name.lower() for name in args.exclude_tools]
selected_tools = [
    tool
    for tool in TOOLS
    if tool.name.lower() in selected_tool_names
    and tool.name.lower() not in excluded_tool_names
]
selected_tool_names = [tool.name for tool in selected_tools]

LOGS = []
for log_file in log_dir.iterdir():
    if not log_file.suffix == ".json":
        continue
    with open(log_file) as f:
        log = json.load(f)
        if log["tool"] in selected_tool_names and log["time"] > 0.01:
            LOGS.append(log)

if not LOGS:
    print("No data to plot")
    exit(1)

DATA = pd.json_normalize(LOGS)
DATA["memory"] /= 1000  # KB -> MB
DATA = DATA.sort_values(
    by=[
        "reads",
        "threads",
        "num_patterns",
    ]
)
KS = DATA["k"].unique()
READS = DATA["reads"].unique()
THREADS = DATA["threads"].unique()
NUM_PATTERNS = DATA["num_patterns"].unique()
NAMES = DATA["tool"].unique()
selected_tool_names = [name for name in selected_tool_names if name in NAMES]

sns.set_context("talk")

if args.versus == "num_patterns":
    for k, threads, reads in itertools.product(KS, THREADS, READS):
        reads_name = basename(pathlib.Path(reads))
        data = DATA.loc[
            (DATA["k"] == k) & (DATA["threads"] == threads) & (DATA["reads"] == reads)
        ]

        plt.figure()
        ax = sns.lineplot(
            data=data,
            x="num_patterns",
            y="time",
            hue="tool",
            hue_order=selected_tool_names,
            palette=PALETTE,
            style="random",
            markers=True,
            linewidth=2.5,
        )

        plt.xscale("log", base=2)
        plt.yscale("log", base=10)
        plt.xlabel("# $k$-mers of interest")
        plt.ylabel("CPU time (s)")
        plt.grid(axis="y", which="major", color="lightgray", linestyle="--")

        handles, labels = plt.gca().get_legend_handles_labels()
        labels[0] = "Tool"
        labels[len(selected_tool_names) + 1] = ""
        labels[len(selected_tool_names) + 2] = "positive"
        labels[len(selected_tool_names) + 3] = "negative"
        plt.legend(
            handles,
            labels,
            title="",
            loc="upper left",
            bbox_to_anchor=(1, 1),
            bbox_transform=plt.gca().transAxes,
        )

        plt.gcf().set_size_inches(10, 5.5)

        for format in args.format:
            out = plots_dir / f"plot_time_k{k}_t{threads}_{reads_name}.{format}"
            plt.savefig(
                out,
                bbox_inches="tight",
                dpi=300,
            )

        plt.figure()
        ax = sns.lineplot(
            data=data,
            x="num_patterns",
            y="memory",
            hue="tool",
            hue_order=selected_tool_names,
            palette=PALETTE,
            style="random",
            markers=True,
            linewidth=2.5,
        )

        plt.xscale("log", base=2)
        plt.yscale("log", base=10)
        plt.xlabel("# $k$-mers of interest")
        plt.ylabel("RAM usage (MB)")
        plt.grid(axis="y", which="major", color="lightgray", linestyle="--")

        handles, labels = plt.gca().get_legend_handles_labels()
        labels[0] = "Tool"
        labels[len(selected_tool_names) + 1] = ""
        labels[len(selected_tool_names) + 2] = "positive"
        labels[len(selected_tool_names) + 3] = "negative"
        plt.legend(
            handles,
            labels,
            title="",
            loc="upper left",
            bbox_to_anchor=(1, 1),
            bbox_transform=plt.gca().transAxes,
        )

        plt.gcf().set_size_inches(10, 5.5)

        for format in args.format:
            out = plots_dir / f"plot_memory_k{k}_t{threads}_{reads_name}.{format}"
            plt.savefig(
                out,
                bbox_inches="tight",
                dpi=300,
            )
elif args.versus == "threads":
    for k, n, reads in itertools.product(KS, NUM_PATTERNS, READS):
        reads_name = basename(pathlib.Path(reads))
        data = DATA.loc[
            (DATA["k"] == k) & (DATA["num_patterns"] == n) & (DATA["reads"] == reads)
        ]

        plt.figure()
        ax = sns.lineplot(
            data=data,
            x="threads",
            y="time",
            hue="tool",
            hue_order=selected_tool_names,
            palette=PALETTE,
            style="random",
            markers=True,
            linewidth=2.5,
        )

        plt.ylim(bottom=0)
        plt.xlabel("# threads")
        plt.ylabel("CPU time (s)")
        plt.grid(axis="y", which="major", color="lightgray", linestyle="--")

        handles, labels = plt.gca().get_legend_handles_labels()
        labels[0] = "Tool"
        labels[len(selected_tool_names) + 1] = ""
        labels[len(selected_tool_names) + 2] = "positive"
        labels[len(selected_tool_names) + 3] = "negative"
        plt.legend(
            handles,
            labels,
            title="",
            loc="upper left",
            bbox_to_anchor=(1, 1),
            bbox_transform=plt.gca().transAxes,
        )

        plt.gcf().set_size_inches(10, 5.5)

        for format in args.format:
            out = plots_dir / f"plot_time_vs_t_k{k}_n{n}_{reads_name}.{format}"
            plt.savefig(
                out,
                bbox_inches="tight",
                dpi=300,
            )

        plt.figure()
        ax = sns.lineplot(
            data=data,
            x="threads",
            y="memory",
            hue="tool",
            hue_order=selected_tool_names,
            palette=PALETTE,
            style="random",
            markers=True,
            linewidth=2.5,
        )

        plt.ylim(bottom=0)
        plt.xlabel("# threads")
        plt.ylabel("RAM usage (MB)")
        plt.grid(axis="y", which="major", color="lightgray", linestyle="--")

        handles, labels = plt.gca().get_legend_handles_labels()
        labels[0] = "Tool"
        labels[len(selected_tool_names) + 1] = ""
        labels[len(selected_tool_names) + 2] = "positive"
        labels[len(selected_tool_names) + 3] = "negative"
        plt.legend(
            handles,
            labels,
            title="",
            loc="upper left",
            bbox_to_anchor=(1, 1),
            bbox_transform=plt.gca().transAxes,
        )

        plt.gcf().set_size_inches(10, 5.5)

        for format in args.format:
            out = plots_dir / f"plot_memory_vs_t_k{k}_n{n}_{reads_name}.{format}"
            plt.savefig(
                out,
                bbox_inches="tight",
                dpi=300,
            )
elif args.versus == "k":
    for t, n, reads in itertools.product(THREADS, NUM_PATTERNS, READS):
        reads_name = basename(pathlib.Path(reads))
        data = DATA.loc[
            (DATA["threads"] == t)
            & (DATA["num_patterns"] == n)
            & (DATA["reads"] == reads)
        ]

        plt.figure()
        ax = sns.lineplot(
            data=data,
            x="k",
            y="time",
            hue="tool",
            hue_order=selected_tool_names,
            palette=PALETTE,
            style="random",
            markers=True,
            linewidth=2.5,
        )

        plt.ylim(bottom=0)
        plt.xlabel("$k$-mer size")
        plt.ylabel("CPU time (s)")
        plt.grid(axis="y", which="major", color="lightgray", linestyle="--")

        handles, labels = plt.gca().get_legend_handles_labels()
        labels[0] = "Tool"
        labels[len(selected_tool_names) + 1] = ""
        labels[len(selected_tool_names) + 2] = "positive"
        labels[len(selected_tool_names) + 3] = "negative"
        plt.legend(
            handles,
            labels,
            title="",
            loc="upper left",
            bbox_to_anchor=(1, 1),
            bbox_transform=plt.gca().transAxes,
        )

        plt.gcf().set_size_inches(10, 5.5)

        for format in args.format:
            out = plots_dir / f"plot_time_vs_k_t{t}_n{n}_{reads_name}.{format}"
            plt.savefig(
                out,
                bbox_inches="tight",
                dpi=300,
            )

        plt.figure()
        ax = sns.lineplot(
            data=data,
            x="k",
            y="memory",
            hue="tool",
            hue_order=selected_tool_names,
            palette=PALETTE,
            style="random",
            markers=True,
            linewidth=2.5,
        )

        plt.ylim(bottom=0)
        plt.xlabel("$k$-mer size")
        plt.ylabel("RAM usage (MB)")
        plt.grid(axis="y", which="major", color="lightgray", linestyle="--")

        handles, labels = plt.gca().get_legend_handles_labels()
        labels[0] = "Tool"
        labels[len(selected_tool_names) + 1] = ""
        labels[len(selected_tool_names) + 2] = "positive"
        labels[len(selected_tool_names) + 3] = "negative"
        plt.legend(
            handles,
            labels,
            title="",
            loc="upper left",
            bbox_to_anchor=(1, 1),
            bbox_transform=plt.gca().transAxes,
        )

        plt.gcf().set_size_inches(10, 5.5)

        for format in args.format:
            out = plots_dir / f"plot_memory_vs_k_t{t}_n{n}_{reads_name}.{format}"
            plt.savefig(
                out,
                bbox_inches="tight",
                dpi=300,
            )
