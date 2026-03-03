#!/bin/bash
set -ux

# https://stackoverflow.com/questions/18215973/how-to-check-if-running-as-root-in-a-bash-script
sudo="sudo"
if [ $(id -u) -eq 0 ]; then
    sudo=""
fi

unamemstr=$(uname -m)
if [[ "$unamemstr" == "x86_64" ]]; then
    apt_libs="libhyperscan5 libhyperscan-dev"
else
    apt_libs="libvectorscan5 libvectorscan-dev"
fi

# https://github.com/VectorCamp/vectorscan/wiki/Installation-from-package
if command -v apt >/dev/null 2>&1; then
    ${sudo} apt update
    ${sudo} apt install -y ${apt_libs}
elif command -v brew >/dev/null 2>&1; then
    brew install vectorscan
else
    echo "No supported package manager" >&2
    exit 1
fi

mkdir -p bin
gcc scan/simplegrep.c -o bin/hsgrep -O3 -march=native $(pkg-config --cflags --libs libhs)
