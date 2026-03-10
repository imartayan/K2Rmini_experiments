#!/bin/bash
set -euxo pipefail

tool="bcalm"
repo="https://github.com/GATB/bcalm.git"

if command -v ${tool} >/dev/null 2>&1; then
    exit 0
fi

if ! test -d ${tool}; then
    git clone --recursive ${repo} ${tool}
fi

cd ${tool}
git pull
mkdir -p build
cd build
CMAKE_POLICY_VERSION_MINIMUM=3.5 cmake ..
make -j
cd ../..
mkdir -p bin
cp ${tool}/build/${tool} bin
