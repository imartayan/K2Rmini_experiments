# K2Rmini Experiments

Experiments on [K2Rmini](https://github.com/Malfoy/K2Rmini) and other sequence filtering tools.

## Requirements

Make sure to install the latest Rust version with [rustup](https://rustup.rs/).

You'll also need a Python setup with `pandas`, `matplotlib` and `seaborn` to make the plots, and different development librairies depending on your OS.

### Debian-based distributions

```sh
sudo apt install -y libsqlite3-dev libzstd-dev libhyperscan5 libhyperscan-dev pipx python3-pandas python3-matplotlib python3-seaborn
```

### Fedora-based distributions

```sh
sudo dnf install -y libsq3-devel libzstd-devel hyperscan-devel pipx python3-pandas python3-matplotlib python3-seaborn
```

### macOS

```sh
brew install gnu-time zstd vectorscan pipx
```

## Installation

You can install all the tools using

```sh
bash install.sh
```

This will store all the binaries in the `bin` folder.

## Running experiments

You can run experiments on your desired set of reads (in FASTQ format).
For instance, you can use [these PacBio HiFi reads from HG002](https://s3-us-west-2.amazonaws.com/human-pangenomics/NHGRI_UCSC_panel/HG002/hpp_HG002_NA24385_son_v1/PacBio_HiFi/15kb/m54328_180928_230446.Q20.fastq).

You can adjust the number of repetitions (`-R`), timeout for each command (`-T`), number of threads used by each tool (`j`), *k*-mer size (`-k`) and the directories used to store logs (`-l`) and patterns (`-p`).
A detailed description of each flag is available using `-h`.

```sh
python3 experiments.py -r <READS> -R 5 -T 300 -j 8
```

This script will run multiple tools and store the results of each run in the `log` folder.

### Plotting the results

Once some results are available in the `log` folder, you can generate plots comparing the runtime and memory usage of the different tools.

You can change the output format (`-f`), tools shown (`-s`) or excluded (`-x`) from the plots, and the directories used for the logs (`-l`) and plots (`-p`).

Three types of plots are available:
- time/memory vs number of patterns `--versus num_patterns` (default)
- time/memory vs number of threads using `--versus threads`
- time/memory vs *k*-mer size using `--versus k`

```sh
python3 plot.py -f pdf png
```

## Experiments from the paper

```sh
# varying number of patterns
python3 experiments.py -r <READS> -R 5 -T 300 -k 31 -j 1 8 -l log
python3 plot.py -f pdf png --versus num_patterns -l log

# varying number of threads
python3 experiments.py -r <READS> -R 5 -T 300 -k 31 -n 1048576 -j 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 -l logt -s k2rmini deacon sbwt bts cleanifier
python3 plot.py -f pdf png --versus threads -l logt

# varying k-mer size
python3 experiments.py -r <READS> -R 5 -T 300 -j 1 -n 1048576 -k 31 39 47 55 63 71 79 87 -l logk -s k2rmini deacon sbwt bts
python3 plot.py -f pdf png --versus k -l logk
```
