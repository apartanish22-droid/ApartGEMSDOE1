#!/usr/bin/env bash
# Fail-closed data preflight. This script does not attempt unauthenticated
# downloads or use owner-supplied mirrors as organizer-authenticated inputs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$ROOT/data"
mkdir -p "$DATA_DIR"

cat <<EOF
Competition data are not downloaded by this script.
The DrivenData data tab is login-gated. On an authorized machine, obtain the
official sample_submission.tif, labels/features, and required catalogue files
from the competition page; verify provenance and hashes, then place them in:
  $DATA_DIR
No public mirror is treated as organizer-authenticated here.
EOF

cd "$ROOT"
python scripts/prepare_data.py
