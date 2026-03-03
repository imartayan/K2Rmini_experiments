import os
import typing

from tool import Tool, basename


def get_param(
    key: typing.Any, params: typing.Any, default: typing.Any | None = None
) -> typing.Any:
    if key in params:
        return params[key]
    elif default is not None:
        print(f"Using {key}={default} by default")
        return default
    else:
        raise Exception(f"{key} is missing from params")


def k2rmini_cmd(
    patterns: os.PathLike,
    reads: os.PathLike,
    **params,
) -> str:
    k = get_param("k", params, 31)
    m = get_param("m", params, 21)
    t = get_param("threshold", params, 0.8)
    T = get_param("threads", params, 8)
    return [f"K2Rmini -k {k} -m {m} -t {t} -T {T} -p {patterns} {reads} -o /dev/null"]


def bts_cmd(
    patterns: os.PathLike,
    reads: os.PathLike,
    **params,
) -> str:
    k = get_param("k", params, 31)
    t = get_param("threads", params, 8)
    threshold = get_param("threshold", params, 0.8)
    if threshold < 1:
        m = round(threshold * 100)
        return [
            f"back_to_sequences -k {k} -m {m} -t {t} --in-kmers {patterns} --in-sequences {reads} --out-sequences /dev/null"
        ]
    else:
        m = round(threshold)
        return [
            f"back_to_sequences -k {k} -m {m} -t {t} --in-kmers {patterns} --in-sequences {reads} --out-sequences /dev/null"
        ]


def grep_cmd(
    patterns: os.PathLike,
    reads: os.PathLike,
    **params,
) -> str:
    if get_param("threads", params, 8) > 1:
        print(f"Skipping grep since it's not multithreaded")
        return []
    patterns_txt = patterns.with_suffix(".txt")
    return [f"grep -Ff {patterns_txt} -B1 {reads} | wc -l; test $? -le 1"]


def ripgrep_cmd(
    patterns: os.PathLike,
    reads: os.PathLike,
    **params,
) -> str:
    j = get_param("threads", params, 8)
    patterns_txt = patterns.with_suffix(".txt")
    return [
        f"rg -j {j} --no-unicode -Ff {patterns_txt} -B1 {reads} > /dev/null; test $? -le 1"
    ]


def hyperscan_cmd(
    patterns: os.PathLike,
    reads: os.PathLike,
    **params,
) -> str:
    if get_param("threads", params, 8) > 1:
        print(f"Skipping hsgrep since it's not multithreaded")
        return []
    patterns_txt = patterns.with_suffix(".txt")
    return [f"hsgrep {patterns_txt} {reads} > /dev/null"]


def seqkit_cmd(
    patterns: os.PathLike,
    reads: os.PathLike,
    **params,
) -> str:
    j = get_param("threads", params, 8)
    patterns_txt = patterns.with_suffix(".txt")
    return [f"seqkit grep -j {j} -sP -f {patterns_txt} {reads} > /dev/null"]


def fqgrep_cmd(
    patterns: os.PathLike,
    reads: os.PathLike,
    **params,
) -> str:
    t = get_param("threads", params, 8)
    patterns_txt = patterns.with_suffix(".txt")
    return [f"fqgrep -t {t} -Ff {patterns_txt} {reads} > /dev/null; test $? -le 1"]


def grepq_cmd(
    patterns: os.PathLike,
    reads: os.PathLike,
    **params,
) -> str:
    j = get_param("threads", params, 8)
    patterns_txt = patterns.with_suffix(".txt")
    return [f"grepq -j {j} -F {patterns_txt} {reads} > /dev/null"]


os.environ["PATH"] = "bin" + os.pathsep + os.environ["PATH"]

K2RMINI = Tool("K2Rmini", k2rmini_cmd)
BTS = Tool("BTS", bts_cmd)
GREP = Tool("Grep", grep_cmd)
RIPGREP = Tool("Ripgrep", ripgrep_cmd)
HYPERSCAN = Tool("Hyperscan", hyperscan_cmd)
SEQKIT = Tool("Seqkit", seqkit_cmd)
FQGREP = Tool("fqgrep", fqgrep_cmd)
GREPQ = Tool("grepq", grepq_cmd)

TOOLS = [GREP, RIPGREP, HYPERSCAN, SEQKIT, FQGREP, GREPQ, BTS, K2RMINI]
