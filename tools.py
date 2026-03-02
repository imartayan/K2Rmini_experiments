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
    if isinstance(threshold, float):
        m = round(threshold * 100)
        return [
            f"back_to_sequences -k {k} -m {m} -t {t} --in-kmers {patterns} --in-sequences {reads} --out-sequences /dev/null"
        ]
    else:
        m = 100
        return [
            f"back_to_sequences -k {k} -m {m} -t {t} --in-kmers {patterns} --in-sequences {reads} --out-sequences /dev/null"
        ]


def grep_cmd(
    patterns: os.PathLike,
    reads: os.PathLike,
    **params,
) -> str:
    T = get_param("threads", params, 8)
    patterns_txt = patterns.with_suffix(".txt")
    return [f"grep -Ff {patterns_txt} -B1 {reads} > /dev/null"]


os.environ["PATH"] = "bin" + os.pathsep + os.environ["PATH"]

K2RMINI = Tool("K2Rmini", k2rmini_cmd)
BTS = Tool("BTS", bts_cmd)
GREP = Tool("grep", grep_cmd)

TOOLS = [K2RMINI, BTS, GREP]
