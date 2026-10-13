#!/usr/bin/env bash
# Compares the ML consumer code in git with the files that actually run on the
# GPU VM. Report only: it never changes anything on either side.
#
# Usage: scripts/gpu-drift.sh [dev|prod|all] [git-ref]      (defaults: all HEAD)
#
# The GPU VM is assembled by hand (no git, no CI/CD), so files there drift from
# the repo. Run this before and after copying a change to the VM. Compared:
#   projects/<svc>/consumer.py and src/**.py  <->  ~/proteng-gpu/apps[-prod]/<svc>/...
#   pkg/common/**.py                           <->  ~/proteng-gpu/app/pkg/common/...
# and, when the private devops-infra repo is cloned next to this one, the VM's
# own scripts (kept there, not here, because this repo is public):
#   devops-infra gpu-vm/{bin,tunnels}/*        <->  ~/proteng-gpu/{bin,tunnels}/*
#   devops-infra gpu-vm/run_forever.sh         <->  every service's run_forever.sh
# Git content is hashed straight from the ref, so Windows CRLF checkouts do not
# show up as false differences. INFRA_DIR and INFRA_REF (default ../devops-infra
# at HEAD) choose where the scripts are read from.
#
# Output lines: DIFF / MISSING-ON-VM / ONLY-ON-VM <vm path> (SAME too with
# VERBOSE=1), then a summary. Exit code is 0 unless the ssh call fails
# (STRICT=1: 1 on any drift). GPU_SSH overrides how the VM is reached
# (default: ssh proteng-gpu).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
which="${1:-all}"
ref="${2:-HEAD}"
GPU_SSH="${GPU_SSH:-ssh proteng-gpu}"
SERVICES="blast mmseqs2 evotune fittop mutation"

case "$which" in
  dev) bases="apps" ;;
  prod) bases="apps-prod" ;;
  all) bases="apps apps-prod" ;;
  *) echo "usage: scripts/gpu-drift.sh [dev|prod|all] [git-ref]" >&2; exit 2 ;;
esac
git -C "$ROOT" rev-parse --verify -q "$ref^{commit}" >/dev/null || { echo "error: unknown git ref: $ref" >&2; exit 2; }

INFRA_DIR="${INFRA_DIR:-$ROOT/../devops-infra}"
INFRA_REF="${INFRA_REF:-HEAD}"
infra_ok=false
if git -C "$INFRA_DIR" rev-parse --verify -q "$INFRA_REF^{commit}" >/dev/null 2>&1 &&
  [ -n "$(git -C "$INFRA_DIR" ls-tree --name-only "$INFRA_REF" -- gpu-vm 2>/dev/null)" ]; then
  infra_ok=true
fi

tracked() { git -C "$ROOT" ls-tree -r --name-only "$ref" -- "$@"; }
infra_tracked() { git -C "$INFRA_DIR" ls-tree -r --name-only "$INFRA_REF" -- "$@"; }
# Hashes "<repo>:<path>", where repo is kf (this repo) or infra (devops-infra).
hash_of() {
  case "$1" in
    infra:*) git -C "$INFRA_DIR" show "$INFRA_REF:${1#infra:}" ;;
    *) git -C "$ROOT" show "$ref:${1#kf:}" ;;
  esac | md5sum | cut -d' ' -f1
}

# Pairs of "<path on VM relative to ~>\t<repo>:<path in repo>".
pairs=$(
  for base in $bases; do
    for svc in $SERVICES; do
      tracked "projects/$svc/consumer.py" "projects/$svc/src" | { grep -E '\.py$' || true; } | while read -r p; do
        printf 'proteng-gpu/%s/%s/%s\tkf:%s\n' "$base" "$svc" "${p#projects/"$svc"/}" "$p"
      done
      if [ "$infra_ok" = true ] && [ -n "$(infra_tracked gpu-vm/run_forever.sh)" ]; then
        printf 'proteng-gpu/%s/%s/run_forever.sh\tinfra:gpu-vm/run_forever.sh\n' "$base" "$svc"
      fi
    done
  done
  tracked pkg/common | { grep -E '\.py$' || true; } | while read -r p; do
    printf 'proteng-gpu/app/%s\tkf:%s\n' "$p" "$p"
  done
  if [ "$infra_ok" = true ]; then
    infra_tracked gpu-vm/bin gpu-vm/tunnels | while read -r p; do
      printf 'proteng-gpu/%s\tinfra:%s\n' "${p#gpu-vm/}" "$p"
    done
  fi
)
if [ "$infra_ok" != true ]; then
  echo "note: $INFRA_DIR has no gpu-vm/ at $INFRA_REF, the VM's own scripts were not compared" >&2
fi

# One ssh call: hash every expected file, then list the .py files that exist,
# so files added by hand on the VM show up too.
# shellcheck disable=SC2016 # runs on the VM.
remote_script='cd ~ || exit 1
while IFS= read -r f; do
  [ -n "$f" ] || continue
  if [ -f "$f" ]; then md5sum "$f"; else echo "MISSING $f"; fi
done
echo "--- files"
for base in '"$bases"'; do
  for svc in '"$SERVICES"'; do
    d="proteng-gpu/$base/$svc"
    [ -f "$d/consumer.py" ] && echo "$d/consumer.py"
    [ -d "$d/src" ] && find "$d/src" -name "*.py" -not -path "*/__pycache__/*"
  done
done
[ -d proteng-gpu/app/pkg/common ] && find proteng-gpu/app/pkg/common -name "*.py" -not -path "*/__pycache__/*"
true'

# shellcheck disable=SC2086 # GPU_SSH is a command prefix such as "ssh proteng-gpu".
if ! remote=$(cut -f1 <<<"$pairs" | $GPU_SSH "$remote_script"); then
  echo "error: could not reach the GPU VM with: $GPU_SSH" >&2
  exit 1
fi

declare -A vm_hash=() vm_files=() expected=()
section=hashes
while IFS= read -r line; do
  if [ "$line" = "--- files" ]; then section=files; continue; fi
  if [ "$section" = hashes ]; then
    case "$line" in
      MISSING\ *) vm_hash["${line#MISSING }"]=MISSING ;;
      *)
        # md5sum prints "<hash>  <path>" (text mode) or "<hash> *<path>" (binary mode).
        path=${line#* }
        path=${path#[ *]}
        vm_hash["$path"]="${line%% *}"
        ;;
    esac
  elif [ -n "$line" ]; then
    vm_files["$line"]=1
  fi
done <<<"$remote"

same=0 diff=0 missing=0 extra=0
while IFS=$'\t' read -r vm repo; do
  [ -n "$vm" ] || continue
  expected["$vm"]=1
  got="${vm_hash[$vm]:-MISSING}"
  if [ "$got" = MISSING ]; then
    echo "MISSING-ON-VM $vm (repo: $repo)"
    missing=$((missing + 1))
  elif [ "$got" = "$(hash_of "$repo")" ]; then
    same=$((same + 1))
    if [ "${VERBOSE:-}" = 1 ]; then echo "SAME $vm"; fi
  else
    echo "DIFF $vm (repo: $repo)"
    diff=$((diff + 1))
  fi
done <<<"$pairs"

for f in "${!vm_files[@]}"; do
  if [ -z "${expected[$f]:-}" ]; then
    echo "ONLY-ON-VM $f"
    extra=$((extra + 1))
  fi
done

echo "SUMMARY ref=$ref envs=$which same=$same diff=$diff missing-on-vm=$missing only-on-vm=$extra"
if [ "${STRICT:-}" = 1 ] && [ $((diff + missing + extra)) -gt 0 ]; then
  exit 1
fi
