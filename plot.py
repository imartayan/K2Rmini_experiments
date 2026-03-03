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
PALETTE = {
    k: v
    for k, v in zip(
        TOOL_NAMES,
        [
            "#E15759",
            "#F28E2B",
            "#EDC948",
            "#59A14F",
            "#76B7B2",
            "#FF9DA7",
            "#B07AA1",
            "#4E79A7",
        ],
    )
}

parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    "--format",
    help="plot format ['pdf']",
    type=str,
    default="pdf",
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
    help="pattern directory ['plots']",
    type=str,
    default="plots",
)

args = parser.parse_args()
log_dir = pathlib.Path(args.log_dir)
plots_dir = pathlib.Path(args.plots_dir)
plots_dir.mkdir(exist_ok=True)


LOGS = []
for log_file in log_dir.iterdir():
    if not log_file.suffix == ".json":
        continue
    with open(log_file) as f:
        log = json.load(f)
        if log["tool"] in TOOL_NAMES and log["time"] > 0:
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

sns.set_context("talk")

for k, reads, threads in itertools.product(KS, READS, THREADS):
    data = DATA.loc[
        (DATA["k"] == k) & (DATA["reads"] == reads) & (DATA["threads"] == threads)
    ]

    reads_name = basename(pathlib.Path(reads))
    out = plots_dir / f"plot_time_k{k}_t{threads}_{reads_name}.{args.format}"

    plt.figure()
    ax = sns.lineplot(
        data=data,
        x="num_patterns",
        y="time",
        hue="tool",
        hue_order=TOOL_NAMES,
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
    labels[len(TOOL_NAMES) + 1] = ""
    labels[len(TOOL_NAMES) + 2] = "positive"
    labels[len(TOOL_NAMES) + 3] = "negative"
    plt.legend(
        handles,
        labels,
        title="",
        loc="upper left",
        bbox_to_anchor=(1, 1),
        bbox_transform=plt.gca().transAxes,
    )

    plt.gcf().set_size_inches(10, 5.5)

    plt.savefig(
        out,
        bbox_inches="tight",
        dpi=300,
    )
