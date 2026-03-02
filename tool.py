import json
import os
import pathlib
import platform
import subprocess
import sys
import typing


GNU_TIME = "/usr/bin/time" if platform.system() == "Linux" else "gtime"
LOG_DIR = pathlib.Path("log")


def basename(filepath: os.PathLike) -> str:
    if filepath.suffixes:
        first_suffix = filepath.suffixes[0]
        return filepath.name.split(first_suffix)[0]
    else:
        return filepath.name


def update_json(json_file: os.PathLike, **fields) -> typing.NoReturn:
    if json_file.exists():
        with open(json_file, "r") as f:
            data = json.load(f)
            data |= fields
    else:
        data = fields
    with open(json_file, "w+") as f:
        json.dump(data, f)


def execute(
    command: str, timeout: float | None = None, silent: bool = False
) -> tuple[str | None, str | None]:
    try:
        proc = subprocess.run(
            command,
            shell=True,
            check=True,
            timeout=timeout,
            capture_output=True,
            text=True,
        )
        out, err = proc.stdout, proc.stderr
        if not silent and out is not None and len(out) > 0:
            sys.stdout.write(out + "\n")
        if not silent and err is not None and len(err) > 0:
            sys.stderr.write(err + "\n")
        return out, err
    except subprocess.SubprocessError as proc:
        if isinstance(proc, subprocess.TimeoutExpired):
            print(f"timed out after {timeout}s")
            return None, None
        out, err = proc.stdout, proc.stderr
        if isinstance(out, bytes):
            out = out.decode("utf-8")
        if not silent and isinstance(out, str) and len(out) > 0:
            sys.stdout.write(out + "\n")
        if isinstance(err, bytes):
            err = err.decode("utf-8")
        if not silent and isinstance(err, str) and len(err) > 0:
            sys.stderr.write(err + "\n")
        return None, None


class Tool:
    def __init__(
        self,
        name: str,
        cmd,
        postprocess=None,  # time, memory, out, err -> time, memory
    ):
        assert name
        assert cmd
        self.name = name
        self.cmd = cmd
        self.postprocess = postprocess

    # adapt arguments depending on the benchmark
    def log_file(
        self,
        patterns: os.PathLike,
        reads: os.PathLike,
        log_dir: os.PathLike = LOG_DIR,
        **params,
    ) -> os.PathLike:
        filename = "_".join(
            [self.name, basename(reads), basename(patterns)]
            # + [f"{k}{v}" for (k, v) in params.items()]  # too long?
        )
        return log_dir / f"{filename}.json"

    # adapt arguments depending on the benchmark
    def run(
        self,
        patterns: os.PathLike,
        reads: os.PathLike,
        repeat: int = 1,
        timeout: float | None = None,
        overwrite_log: bool = False,
        log_dir: os.PathLike = LOG_DIR,
        **params,
    ) -> typing.NoReturn:
        log_file = self.log_file(patterns, reads, log_dir=log_dir, **params)
        if log_file.exists() and not overwrite_log:
            print(f"Log already exists: {log_file}")
            return

        commands = self.cmd(patterns, reads, **params)  # adapt args
        total_time, total_memory = 0, 0
        for _ in range(repeat):
            for command in commands:
                sys.stderr.write(f"$ {command}\n")
                out, err = execute(f"{GNU_TIME} -f '%e %M' {command}", timeout=timeout)
                try:
                    time, memory = list(map(float, err.splitlines()[-1].split()))
                    total_time += time
                    total_memory = max(total_memory, memory)
                except Exception:
                    print(f"{self.name} failed during execution")
                    return
        time = total_time / repeat
        memory = total_memory / repeat

        if self.postprocess is not None:
            time, memory = self.postprocess(time, memory, out, err)

        update_json(
            log_file,
            tool=self.name,
            reads=str(reads),
            patterns=str(patterns),
            time=time,
            memory=memory,
            **params,
        )
