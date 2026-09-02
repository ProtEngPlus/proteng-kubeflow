#!/bin/sh
set -u

: "${HTTP_PROXY:=http://localhost:18888}"
: "${HTTPS_PROXY:=http://localhost:18888}"
: "${NCBI_EMAIL:?ต้อง export NCBI_EMAIL=<อีเมลจริง> ก่อนรัน}"
export HTTP_PROXY HTTPS_PROXY

BATCHES=3
TRIALS=10
GAP=21600                       # เว้นระหว่าง batch = 6 ชม.
OUT="$HOME/ncbi_throughput.csv" # script append ต่อไฟล์เดิม

b=1
while [ "$b" -le "$BATCHES" ]; do
    echo "=== batch $b/$BATCHES  $(date -u '+%Y-%m-%dT%H:%M:%SZ') ==="
    venv/bin/python -u ncbi_throughput_test.py --trials "$TRIALS" --outfile "$OUT"
    b=$((b + 1))
    [ "$b" -le "$BATCHES" ] && sleep "$GAP"
done
echo "=== done  $(date -u '+%Y-%m-%dT%H:%M:%SZ') ==="
