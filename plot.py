import json
import pathlib

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from tools import TOOLS
from tool import basename

LOG_DIR = pathlib.Path("log")
PLOT_DIR = pathlib.Path("plots")
PLOT_DIR.mkdir(exist_ok=True)
PLOT_FORMAT = "png"
FONT_SIZE = 14
MARKER_SIZE = 10

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

LOGS = []
for log_file in LOG_DIR.iterdir():
    if not log_file.is_file():
        continue
    with open(log_file) as f:
        log = json.load(f)
        if log["tool"] in TOOL_NAMES:
            LOGS.append(log)

DATA = pd.json_normalize(LOGS)
DATA["memory"] /= 1000  # KB -> MB
DATA = DATA.sort_values(by=["num_patterns", "threads"])
data = DATA

sns.set_context("talk")

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
    f"{PLOT_DIR}/plot_time_{basename(MAIN_FILE)}.{PLOT_FORMAT}",
    bbox_inches="tight",
    dpi=300,
)
