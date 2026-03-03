# K2Rmini Experiments

## Requirements

Make sure to install the latest Rust version with [rustup](https://rustup.rs/).

You'll also need a Python setup with `pandas`, `matplotlib` and `seaborn` to make the plots.

Other tools may require additional development librairies depending on your setup.

### Debian-based distributions

```sh
sudo apt install libzstd-dev libhyperscan5 libhyperscan-dev
```

### macOS

```sh
brew install vectorscan
```

## Experiments

You can run the experiments on your desired set of reads (in FASTQ format).
For instance, you can use [these PacBio long reads](https://s3-us-west-2.amazonaws.com/human-pangenomics/NHGRI_UCSC_panel/HG002/hpp_HG002_NA24385_son_v1/PacBio_HiFi/15kb/m54328_180928_230446.Q20.fastq).

You can adjust the number of repetitions (`-R`), timeout for each command (`-T`), number of threads used by each tool (`j`), *k*-mer size (`-k`) and the directories used to store logs (`-l`) and patterns (`-p`).
A detailed description of each flag is available using `-h`.

```sh
python3 experiments.py -r <READS> -R 5 -T 300 -j 8
```

This script will run multiple tools and store the results of each run in the `log` folder.

### Plotting the results

On some results are available in the `log` folder, you can generate plots comparing the runtime of the different tools.

You can change the output format (`-f`) and the directories used for the logs (`-l`) and plots (`-p`).

```sh
python3 plot.py -f pdf
```
