#!/bin/bash
set -euxo pipefail

tool="K2Rmini"
repo="https://github.com/Malfoy/K2Rmini.git"

if ! test -d ${tool}; then
    git clone ${repo} ${tool}
fi

cd ${tool}
git pull
RUSTFLAGS="-C target-cpu=native" cargo build --release
cd ..
mkdir -p bin
cp ${tool}/target/release/${tool} bin
