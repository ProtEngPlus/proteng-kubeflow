# NCBI BLAST throughput test

`ncbi_throughput_test.py` runs N `NCBIWWW.qblast` calls back-to-back and records
how long each one takes. Point: get a real latency distribution for BLAST-via-NCBI
(seen anywhere from ~1 min to 45+ min for the same query) instead of an anecdote.

Same effective call as the blast service (`projects/blast/src/service/run_blast.py`):
`blastp` / `nr`, `expect=10.0`, `hitlist_size=50`, socket timeout 180 s. Nothing
from the pipeline is imported (no RabbitMQ, no consumer, no GCS), so the numbers
are NCBI's latency only.

## Run

```sh
export NCBI_EMAIL="you@example.com"
python ncbi_throughput_test.py --trials 15 --outfile results.csv
```

- Needs `biopython` and network access to NCBI. Run it wherever the blast service
  runs, using that service's Python and network path, so the measurement matches
  production.
- Long: 15 trials x (1-45 min). Use `nohup ... &` and `tail -f` the log.
- The CSV is appended and flushed per trial — an interrupted run keeps its rows,
  just run again to add more.
- Don't run it alongside a real BLAST job; two request streams from one IP can
  trip NCBI's rate limit.

## Output

- `results.csv` — one row per trial: `trial,start_utc,duration_s,status,hits,error`
- stdout — a line per trial, then `min / max / mean / median` of the OK trials.

## Running it on the GPU VM (`isel-5090`)

The VM has no checkout of this repo — services live at `~/proteng-gpu/apps/<name>/`
with their own `venv/`. Copy the script in (terminal paste breaks the file — use
`scp`, or `base64 -w0` on one side and `base64 -d` on the other, then check
`md5sum`). Then:

```sh
cd ~/proteng-gpu/apps/blast
export HTTP_PROXY=http://localhost:18888 HTTPS_PROXY=http://localhost:18888
export NCBI_EMAIL="you@example.com"
nohup venv/bin/python ncbi_throughput_test.py \
    --trials 15 --outfile ~/ncbi_throughput.csv > ~/ncbi_throughput.log 2>&1 &
tail -f ~/ncbi_throughput.log
```

`localhost:18888` is the SSH-tunnel HTTP proxy the consumers use. Biopython there
is 1.81 — `NCBIWWW.email` / `.tool` may be a no-op (added in 1.82); harmless, and
it doesn't affect the timings.

## Notes

- Biopython's `qblast` rate-limits itself (poll delay starts at 20 s, rises to
  60 s against the public NCBI host), so sequential calls need no extra throttle.
- `run_blast.py` never sets `NCBIWWW.email` / `NCBIWWW.tool`. Setting both there
  is a cheap NCBI-usage-policy fix worth doing.
