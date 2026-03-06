#!/bin/bash
set -euxo pipefail

mkdir -p bin
gcc scan/simplegrep.c -o bin/hsgrep -O3 -march=native $(pkg-config --cflags --libs libhs)
