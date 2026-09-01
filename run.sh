#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

services=$(cd projects && ls -d */ | tr -d '/' | tr '\n' ' ')
svc="${1:-}"

if [ -z "$svc" ]; then
  echo "usage: ./run.sh <service|all>"
  echo "services: $services"
  exit 1
fi

if [ "$svc" != "all" ]; then
  [ -x "projects/$svc/run.sh" ] || { echo "no such service: $svc"; echo "services: $services all"; exit 1; }
  exec "projects/$svc/run.sh"
fi

pids=()
for s in $services; do
  [ "$s" = "evotune_ESM" ] && [ "${RUN_ESM:-0}" != "1" ] && { echo ">> skip $s (set RUN_ESM=1 to include)"; continue; }
  [ -x "projects/$s/run.sh" ] || continue
  echo ">> starting $s"
  ( "projects/$s/run.sh" 2>&1 | sed "s/^/[$s] /" ) &
  pids+=($!)
done

trap 'echo; echo ">> stopping ${#pids[@]} services"; kill "${pids[@]}" 2>/dev/null; wait 2>/dev/null; exit 0' INT TERM
echo ">> ${#pids[@]} services running - Ctrl-C to stop all"
wait
