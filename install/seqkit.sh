#!/bin/bash
set -euxo pipefail

if command -v "seqkit" >/dev/null 2>&1; then
    exit 0
fi

version=$(curl -s https://api.github.com/repos/shenwei356/seqkit/releases/latest | jq -r '.tag_name')

# https://stackoverflow.com/questions/394230/how-to-detect-the-os-from-a-bash-script
unamestr=$(uname)
if [[ "$unamestr" == "Linux" ]]; then
    platform="linux"
elif [[ "$unamestr" == "Darwin" ]]; then
    platform="darwin"
else
    echo "Unknown platform: ${unamestr}"
    exit 1
fi

arch="unknown"
unamemstr=$(uname -m)
if [[ "$unamemstr" == "x86_64" ]]; then
    arch="amd64"
elif [[ "$unamemstr" == "arm64" ]]; then
    arch="arm64"
else
    echo "Unknown architecture: ${unamemstr}"
    exit 1
fi

mkdir -p bin
cd bin
wget -O seqkit.tar.gz https://github.com/shenwei356/seqkit/releases/download/${version}/seqkit_${platform}_${arch}.tar.gz
tar -xf seqkit.tar.gz
rm seqkit.tar.gz
