#!/usr/bin/env bash
# Creates projects/<service>/.venv with that service's dependencies.
#
# Usage: scripts/venv.sh <service>        (for example: scripts/venv.sh mmseqs2)
#
# The pinned versions in requirements.txt have no wheels for current Python and
# do not build from source, so the pins are stripped and pip picks compatible
# versions (a known source of drift, see explanation/known-issues.md in the
# manual-guides repo). Per-service fixes applied here:
#   - mmseqs2: skip the legacy `bson` package; pymongo already provides bson.
#   - evotune, evotune_ESM, fittop, mutation: jax-unirep needs setuptools<81
#     (pkg_resources) and the jax.numpy.clip patch in dev_tools/patches.
# Running it again on an existing .venv only installs what is missing.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
svc="${1:-}"
[ -n "$svc" ] || { echo "usage: scripts/venv.sh <service>" >&2; exit 2; }
dir="$ROOT/projects/$svc"
[ -f "$dir/requirements.txt" ] || { echo "error: no such service: $svc" >&2; exit 2; }

# python3 on Windows is often the Microsoft Store stub, so test that it runs.
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  if python3 -c 'import sys' >/dev/null 2>&1; then PY=python3; else PY=python; fi
fi

cd "$dir"
if [ ! -d .venv ]; then
  echo ">> creating $svc/.venv with $("$PY" --version 2>&1)"
  "$PY" -m venv .venv
fi
if [ -x .venv/Scripts/python.exe ]; then VPY=.venv/Scripts/python.exe; else VPY=.venv/bin/python; fi

"$VPY" -m pip install --quiet --upgrade pip

# Pins are stripped, except for packages whose newer major versions changed the
# API the code uses. jax-unirep 3.x (2026) is not compatible with the 2.2.0 API
# (layers module, get_reps params) that evotune/fittop/mutation and the patch
# rely on; it is pure Python, so keeping its pin never blocks the install.
KEEP_PINS='^(jax-unirep|jax_unirep)[=<>~!]'
req=.venv/requirements-unpinned.txt
{
  grep -E "$KEEP_PINS" requirements.txt || true
  grep -vE "$KEEP_PINS" requirements.txt | sed -E 's/[=<>~!].*$//; s/[[:space:]]+$//'
} | grep -vE '^[[:space:]]*(#|$)' >"$req"

jax_service=false
case "$svc" in
  mmseqs2) sed -i '/^bson$/d' "$req" ;;
  evotune | evotune_ESM | fittop | mutation) jax_service=true ;;
esac

if [ "$jax_service" = true ]; then
  "$VPY" -m pip install --quiet "setuptools<81"
fi

echo ">> installing dependencies for $svc (this can take several minutes)"
"$VPY" -m pip install --quiet -r "$req" -r "$ROOT/pkg/common/requirements.txt"

if [ "$jax_service" = true ]; then
  activations=$("$VPY" -c 'import importlib.util as u; print(u.find_spec("jax_unirep").submodule_search_locations[0])')/activations.py
  "$VPY" "$ROOT/dev_tools/patches/fix_jax_unirep.py" "$activations"
fi

echo ">> $svc/.venv ready ($("$VPY" --version 2>&1))"
