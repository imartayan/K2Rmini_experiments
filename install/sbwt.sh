#!/bin/bash
set -euxo pipefail

tool="sbwt_filter"

cd ${tool}
RUSTFLAGS="-C target-cpu=native" cargo build --release
cd ..
mkdir -p bin
cp ${tool}/target/release/${tool} bin
