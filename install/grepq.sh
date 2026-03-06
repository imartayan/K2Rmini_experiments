#!/bin/bash
set -euxo pipefail

tool="grepq"
repo="https://github.com/imartayan/grepq.git"
branch="fix"

if ! test -d ${tool}; then
    git clone ${repo} ${tool} --branch ${branch}
fi

cd ${tool}
git pull
RUSTFLAGS="-C target-cpu=native" cargo build --release
cd ..
mkdir -p bin
cp ${tool}/target/release/${tool} bin
