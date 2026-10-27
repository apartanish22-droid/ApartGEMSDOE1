#!/usr/bin/env bash
# Compatibility wrapper. These owner-hosted files are NOT authenticated
# organizer downloads. All restored bytes are pinned by size and SHA-256.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
echo "Restoring hash-pinned owner mirrors only; official origin and upload authorization are not established." >&2
exec python3 "$root/scripts/restore_inputs.py" --group light "$@"
