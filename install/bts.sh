#!/bin/bash
set -euxo pipefail

tool="back_to_sequences"
repo="https://github.com/pierrepeterlongo/back_to_sequences.git"

if ! test -d ${tool}; then
    git clone ${repo} ${tool}
fi

cd ${tool}
git pull
RUSTFLAGS="-C target-cpu=native" cargo build --release
cd ..
mkdir -p bin
cp ${tool}/target/release/${tool} bin
