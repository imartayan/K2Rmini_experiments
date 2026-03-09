#!/bin/bash
set -euxo pipefail

if command -v "cleanifier" >/dev/null 2>&1; then
    exit 0
fi

if command -v "pipx" >/dev/null 2>&1; then
    echo "Cannot find pipx"
    exit 1
fi

pipx install cleanifier
