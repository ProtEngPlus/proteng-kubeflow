#!/usr/bin/env bash
# Creates projects/<service>/.venv with that service's dependencies.
#
# Usage: scripts/venv.sh <service>        (for example: scripts/venv.sh mmseqs2)
#        VENV_PYTHON=<python3.10> scripts/venv.sh <service>
#
# The venv uses Python 3.10, the version on the GPU VM, and installs the pins in
# requirements.txt as they are. projects/<service>/constraints.txt is the
# `pip freeze` of that service's venv on the GPU VM, so the indirect
# dependencies also match production. Per-service fixes applied here:
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

is_310() { "$1" -c 'import sys; sys.exit(sys.version_info[:2] != (3, 10))' >/dev/null 2>&1; }

PY="${VENV_PYTHON:-}"
if [ -z "$PY" ]; then
  for candidate in python3.10 python3 python; do
    if is_310 "$candidate"; then PY=$candidate; break; fi
  done
fi
if [ -z "$PY" ] && command -v py >/dev/null 2>&1; then
  PY=$(py -V:3.10 -c 'import sys; print(sys.executable)' 2>/dev/null || true)
fi
if [ -z "$PY" ] || ! is_310 "$PY"; then
  echo "error: the venvs need Python 3.10, the version on the GPU VM" >&2
  echo "  Windows: py install 3.10" >&2
  echo "  Linux/macOS: install python3.10, or point VENV_PYTHON at it" >&2
  exit 2
fi

cd "$dir"
if [ ! -d .venv ]; then
  echo ">> creating $svc/.venv with $("$PY" --version 2>&1)"
  "$PY" -m venv .venv
fi
if [ -x .venv/Scripts/python.exe ]; then VPY=.venv/Scripts/python.exe; else VPY=.venv/bin/python; fi
if ! is_310 "$VPY"; then
  echo "error: projects/$svc/.venv uses $("$VPY" --version 2>&1), not Python 3.10" >&2
  echo "  delete it and run again: rm -rf projects/$svc/.venv" >&2
  exit 2
fi

"$VPY" -m pip install --quiet --upgrade pip

req=.venv/requirements-install.txt
grep -vE '^[[:space:]]*(#|$)' requirements.txt >"$req"
constraints=()
[ -f constraints.txt ] && constraints=(-c constraints.txt)

jax_service=false
case "$svc" in
  mmseqs2) sed -i -E '/^bson([=<>~! ]|$)/d' "$req" ;;
  evotune | evotune_ESM | fittop | mutation) jax_service=true ;;
esac

if [ "$jax_service" = true ]; then
  "$VPY" -m pip install --quiet "setuptools<81"
fi

echo ">> installing dependencies for $svc (this can take several minutes)"
"$VPY" -m pip install --quiet -r "$req" -r "$ROOT/pkg/common/requirements.txt" "${constraints[@]}"

if [ "$jax_service" = true ]; then
  activations=$("$VPY" -c 'import importlib.util as u; print(u.find_spec("jax_unirep").submodule_search_locations[0])')/activations.py
  "$VPY" "$ROOT/dev_tools/patches/fix_jax_unirep.py" "$activations"
fi

echo ">> $svc/.venv ready ($("$VPY" --version 2>&1))"
