#!/bin/bash
set -euxo pipefail

if command -v "deacon" >/dev/null 2>&1; then
    exit 0
fi

RUSTFLAGS="-C target-cpu=native" cargo install deacon
