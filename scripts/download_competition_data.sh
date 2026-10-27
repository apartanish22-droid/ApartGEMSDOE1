#!/usr/bin/env bash
#
# scripts/download_competition_data.sh
#
# Fetch GEMS Prize Challenge (DOE GEMS) competition inputs into data/.
#
# STATUS / BLOCKER (verified):
#   The official competition files (training_features.tif, labels.tif,
#   sample_submission.tif / submission format template, 1m_DEM_links.csv) live
#   behind DrivenData login at
#   https://www.drivendata.org/competitions/306/competition-doe-gems/data/
#   This sandbox has NO DrivenData auth -> those files redirect to login and
#   cannot be auto-downloaded here. Download them manually on any authenticated
#   machine and place them in data/, then re-run this script (it verifies what
#   is present) followed by python scripts/prepare_data.py.
#
# Publicly accessible mirrors / official sources used as fallbacks:
#   - GEMS prize overview PDF (mirror of docs.nlr.gov FY26 OSTI 96647):
#       https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=1
#   - example_submission.tif (submission-format template, mirror):
#       https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=1
#   - existing_faults.tif (USGS/INGENIOUS catalogue raster, mirror):
#       https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=1
#   - gems-geodawn-numerical-features.tif (GeoDAWN numerical feature stack, mirror):
#       https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=1
#   - Digital-elevation-model links JSON (mirror):
#       https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=1
#   - INGENIOUS regional dataset compilation (official DOE GDR, CC-BY 4.0):
#       https://gdr.openei.org/submissions/1391   DOI: 10.15121/1881483
#         files: gravity/magnetics, heat flow, MT conductance, quaternary faults,
#                paleo-geothermal features, wells/springs, study-area boundary, ...
#
set -euo pipefail

DATA_DIR="${1:-data}"
DATA_DIR="$(cd "$(dirname "$0")/.." && pwd)/$DATA_DIR"
mkdir -p "$DATA_DIR"

UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

have() { command -v "$1" >/dev/null 2>&1; }
DL_CMD=""
if have curl; then
  DL_CMD="curl -sL --retry 3 --max-time 120 -A '$UA'"
elif have wget; then
  DL_CMD="wget -q --tries=3 --timeout=120 -U '$UA' -O"
else
  echo "ERROR: neither curl nor wget is available." >&2
  exit 1
fi

mirror() {
  local url="$1" out="$2"
  if [ -f "$out" ]; then
    echo "SKIP (exists): $out"
    return 0
  fi
  echo "FETCH: $url -> $out"
  # eval so the UA string is passed as one argument
  eval "$DL_CMD -o '$out.part' '$url'" && mv "$out.part" "$out" || {
    echo "WARN: failed to fetch $url (network/host may block the sandbox)" >&2
    rm -f "$out.part"
    return 1
  }
}

# NOTE: Dropbox scl/fi links frequently return HTTP 000 / empty bodies from
# restricted egress environments. A failed mirror is NOT a data failure: the
# authoritative source remains the DrivenData data tab (login required).
mirror "https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=1" \
  "$DATA_DIR/GEMS_96647.pdf" || true
mirror "https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=1" \
  "$DATA_DIR/example_submission.tif" || true
mirror "https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=1" \
  "$DATA_DIR/existing_faults.tif" || true
mirror "https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=1" \
  "$DATA_DIR/gems-geodawn-numerical-features.tif" || true
mirror "https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=1" \
  "$DATA_DIR/Digital-elevation-model-links-JSON.pdf" || true

echo "------------------------------------------------------------"
echo "Data dir: $DATA_DIR"
ls -la "$DATA_DIR"
echo "------------------------------------------------------------"
echo "NEXT: place the DrivenData login-gated files (training_features.tif,"
echo "labels.tif, sample_submission.tif) into $DATA_DIR manually, then run:"
echo "  python scripts/prepare_data.py"
echo "Training requires a GPU (reference: unet-mc-cv-reference-solution.ipynb);"
echo "metric / holdout / validation all run on CPU."
