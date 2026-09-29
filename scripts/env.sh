#!/usr/bin/env bash
# Creates projects/<service>/.env from .env.example for every service that has
# no .env yet. Existing .env files are never overwritten.
#
# Usage: scripts/env.sh               (plain copy, GCS credentials left empty)
#        scripts/env.sh --local-gcs   (also point every .env at the local
#                                      fake-gcs emulator on localhost:4443)
#
# STORAGE_EMULATOR_HOST is for local machines only. Never set it on the GPU VM:
# the storage library would then send real jobs to an emulator that is not there.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
local_gcs=false
case "${1:-}" in
  "") ;;
  --local-gcs) local_gcs=true ;;
  *) echo "usage: scripts/env.sh [--local-gcs]" >&2; exit 2 ;;
esac

for example in "$ROOT"/projects/*/.env.example; do
  dir=$(dirname "$example")
  svc=$(basename "$dir")
  if [ ! -f "$dir/.env" ]; then
    cp "$example" "$dir/.env"
    echo ">> $svc: created .env from .env.example"
  fi
  if [ "$local_gcs" = true ]; then
    if grep -q '^STORAGE_EMULATOR_HOST=$' "$dir/.env"; then
      sed -i 's#^STORAGE_EMULATOR_HOST=$#STORAGE_EMULATOR_HOST=http://localhost:4443#' "$dir/.env"
      echo ">> $svc: STORAGE_EMULATOR_HOST=http://localhost:4443"
    elif ! grep -q '^STORAGE_EMULATOR_HOST=' "$dir/.env"; then
      echo "STORAGE_EMULATOR_HOST=http://localhost:4443" >>"$dir/.env"
      echo ">> $svc: STORAGE_EMULATOR_HOST=http://localhost:4443 (appended)"
    fi
  fi
done
