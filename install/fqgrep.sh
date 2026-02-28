#!/bin/bash
set -euxo pipefail

if command -v "fqgrep" >/dev/null 2>&1; then
    exit 0
fi

cargo install fqgrep
