#!/bin/bash
set -euxo pipefail

bash install/pattern.sh
bash install/ggcat.sh
bash install/sbwt.sh
bash install/k2rmini.sh
bash install/deacon.sh
bash install/bts.sh
bash install/ripgrep.sh
bash install/seqkit.sh
bash install/fqgrep.sh
bash install/grepq.sh
bash install/cleanifier.sh
bash install/scan.sh
