#!/bin/bash
set -euxo pipefail

if command -v "grepq" >/dev/null 2>&1; then
    exit 0
fi

cargo install grepq
