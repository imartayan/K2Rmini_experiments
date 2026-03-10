#!/bin/bash
set -euxo pipefail

tool="ggcat"
gh_repo="algbio/ggcat"

if command -v ${tool} >/dev/null 2>&1; then
    exit 0
fi

version=$(curl -s https://api.github.com/repos/${gh_repo}/releases/latest | jq -r '.tag_name')

# https://stackoverflow.com/questions/394230/how-to-detect-the-os-from-a-bash-script
unamestr=$(uname)
if [[ "$unamestr" == "Linux" ]]; then
    platform="unknown-linux-gnu"
elif [[ "$unamestr" == "Darwin" ]]; then
    platform="apple-darwin"
else
    echo "Unknown platform: ${unamestr}"
    exit 1
fi

arch="unknown"
unamemstr=$(uname -m)
if [[ "$unamemstr" == "x86_64" ]]; then
    arch="x86_64"
elif [[ "$unamemstr" == "arm64" ]]; then
    arch="aarch64"
else
    echo "Unknown architecture: ${unamemstr}"
    exit 1
fi

mkdir -p bin
cd bin
wget -O ${tool}.tar.gz https://github.com/${gh_repo}/releases/download/${version}/${tool}-${arch}-${platform}.tar.gz
tar -xf ${tool}.tar.gz
rm ${tool}.tar.gz
