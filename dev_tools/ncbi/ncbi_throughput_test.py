import argparse
import csv
import os
import re
import socket
import statistics
import sys
import time
from datetime import datetime, timezone

from Bio.Blast import NCBIWWW

SEQUENCE = (
    "MSIQFFRVALIPFFAAFCLPVFAHPETLVKVKDAEDQLGARVGYIELDLNSGKILESFRPEERFPMMS"
    "TFKVLLCGAVLSRVDAGQEQLGRRIHYSQNDLVEYSPVTEKHLTDGMTVRELCSAAITMSDNTAANLL"
    "LTTIGGPKELTAFLHNMGDHVTRLDRWEPELNEAIPNDERDTTMPAAMATTLRKLLTGELLTLASRQQ"
    "LIDWMEADKVAGPLLRSALPAGWFIADKSGAGERGSRGIIAALGPDGKPSRIVVIYTTGSQATMDERN"
    "RQIAEIGASLIKHW"
)


def run_trial(n):
    start = time.monotonic()
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = NCBIWWW.qblast(
            "blastp", "nr", SEQUENCE, expect=10.0, hitlist_size=50
        ).read()
        dur = round(time.monotonic() - start, 1)
        hits = len(re.findall(r"<Hit>", result))
        print(f"trial {n}: OK {dur}s, {hits} hits")
        return [n, started, dur, "ok", hits, ""]
    except Exception as err:  # noqa: BLE001
        dur = round(time.monotonic() - start, 1)
        print(f"trial {n}: FAIL {dur}s, {type(err).__name__}: {err}")
        return [n, started, dur, "fail", 0, f"{type(err).__name__}: {err}"]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=15)
    ap.add_argument("--outfile", default="ncbi_throughput.csv")
    args = ap.parse_args(argv)

    socket.setdefaulttimeout(180)
    NCBIWWW.email = os.getenv("NCBI_EMAIL")
    NCBIWWW.tool = "protengplus-throughput-test"
    if not NCBIWWW.email:
        print("warning: NCBI_EMAIL not set")

    rows = []
    new = not os.path.exists(args.outfile) or os.path.getsize(args.outfile) == 0
    with open(args.outfile, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["trial", "start_utc", "duration_s", "status", "hits", "error"])
        for i in range(1, args.trials + 1):
            row = run_trial(i)
            w.writerow(row)
            fh.flush()
            rows.append(row)

    ok = sorted(r[2] for r in rows if r[3] == "ok")
    print(f"\n{len(ok)}/{len(rows)} ok")
    if ok:
        print(
            f"duration_s: min={ok[0]} max={ok[-1]} "
            f"mean={statistics.mean(ok):.1f} median={statistics.median(ok):.1f}"
        )


if __name__ == "__main__":
    main(sys.argv[1:])
