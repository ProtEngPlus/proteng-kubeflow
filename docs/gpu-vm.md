# GPU VM — the ML pipeline runbook

The whole `ml-pipeline` (`blast`, `mmseqs2`, `evotune`, `evotune_ESM`, `fittop`,
`mutation`) runs **off-cluster** on the GPU VM `isel-5090` / `161.200.92.6` (RTX 5090).
Both environments live here:

- **dev** — `~/proteng-gpu/apps/<svc>/` — 6 services (incl. `evotune_ESM`)
- **production** — `~/proteng-gpu/apps-prod/<svc>/` — 5 services (no `evotune_ESM`)

The in-cluster `ml-*` consumer Deployments on the old VM are pinned to `replicas: 0` in
git (see [devops-k8s](#relationship-to-devops-k8s)); the `ml-*-rest` FastAPI Deployments
are dead weight (nothing routes to them) and left alone.

This box is in a **cloud project we don't control**: no `sudo`, no Docker, and its
firewall cannot be changed (only pre-existing NodePorts are allowlisted). Everything below
works within those limits.

> `SETUP.md` in the repo root covers running a service **locally**. This file is the GPU
> VM deployment.

---

## Where everything runs

```text
                       internet
                          │
             ┌────────────┴─────────────┐
  browsers ─▶│  nginx-proxy  (old VM,   │  TLS term, routes by hostname
             │  host Docker, :80/:443)  │
             └────────────┬─────────────┘
                          │  NodePort
        ┌─────────────────┴──────────────────────────────────────┐
        │  OLD VM  34.143.239.15   MicroK8s (single node)         │
        │                                                        │
        │  default ns (dev)            production ns              │
        │   protengplus-web  :30001     :31001                    │
        │   proteng-bff      :30080     :31080                    │
        │   proteng-user-mgmt:30081     :31081                    │
        │   proteng-conductor:30082     :31082                    │
        │   rabbitmq AMQP    :30673     :31673   ◀── the tunnels  │
        │   rabbitmq mgmt    :30072     :31072                    │
        │   ml-* consumers   replicas 0  replicas 0  (served here▼)│
        │   ml-*-rest        :8080 ClusterIP (vestigial)          │
        │   argocd :30098   MongoDB :27017 (host Docker)          │
        └───────────▲───────────────────────▲────────────────────┘
                    │   SSH  (key auth,      │
                    │   ~/.ssh/id_ed25519_oldvm)
        ┌───────────┴───────────────────────┴────────────────────┐
        │  GPU VM  isel-5090 / 161.200.92.6   RTX 5090            │
        │                                                        │
        │  ~/proteng-gpu/tunnels/                                 │
        │    proxy.sh         localhost:18888 ──▶ old VM :8888    │  outbound HTTP
        │    rabbitmq.sh      localhost:5672  ──▶ old VM :30673   │  dev  AMQP
        │    rabbitmq-prod.sh localhost:5673  ──▶ old VM :31673   │  prod AMQP
        │                                                        │
        │  ~/proteng-gpu/apps/<svc>/       (dev,  6 consumers)    │
        │  ~/proteng-gpu/apps-prod/<svc>/  (prod, 5 consumers)    │
        │    consumers have NO inbound port — outbound AMQP +     │
        │    HTTPS (NCBI, GCS) only, all via the tunnels above    │
        │  ~/proteng-gpu/bin/    start/stop/status/healthcheck    │
        └────────────────────────────────────────────────────────┘
```

**Service → host → port**

| service                                                | host                 | dev port                                  | prod port                  | notes                                                                |
| ------------------------------------------------------ | -------------------- | ----------------------------------------- | -------------------------- | -------------------------------------------------------------------- |
| nginx-proxy                                            | old VM (host Docker) | :80 → 443 redirect, :443                  | same                       | TLS term, hostname routing                                           |
| protengplus-web (frontend)                             | old VM MicroK8s      | NodePort 30001                            | NodePort 31001             |                                                                      |
| proteng-bff                                            | old VM MicroK8s      | NodePort 30080                            | NodePort 31080             | also backs `doc.protengplus.com`                                     |
| proteng-user-mgmt                                      | old VM MicroK8s      | NodePort 30081                            | NodePort 31081             |                                                                      |
| proteng-conductor                                      | old VM MicroK8s      | NodePort 30082                            | NodePort 31082             | publishes jobs to RabbitMQ per stage                                 |
| RabbitMQ AMQP (`rabbitmq-svc`)                         | old VM MicroK8s      | **NodePort 30673**                        | **NodePort 31673**         | added by the overlays _only_ for the GPU VM tunnels — keep them      |
| RabbitMQ mgmt UI                                       | old VM MicroK8s      | NodePort 30072                            | NodePort 31072             |                                                                      |
| Argo CD                                                | old VM MicroK8s      | NodePort 30098 (`argocd.protengplus.com`) | —                          |                                                                      |
| MongoDB                                                | old VM (host Docker) | :27017                                    | same container             | not in k8s; consumers here **don't touch it** (conductor owns Mongo) |
| `ml-{blast,mmseqs2,evotune,fittop,mutation}` consumers | **GPU VM**           | `~/proteng-gpu/apps/`                     | `~/proteng-gpu/apps-prod/` | no inbound port; outbound AMQP + HTTPS only                          |
| `evotune_ESM`                                          | GPU VM (dev only)    | `~/proteng-gpu/apps/evotune_ESM`          | —                          | no k8s manifest, no conductor `esm` stage — POC                      |
| `ml-*` consumer Deployments                            | old VM MicroK8s      | **replicas 0**                            | **replicas 0**             | served from the GPU VM                                               |
| `ml-*-rest` (5 FastAPI)                                | old VM MicroK8s      | ClusterIP :8080                           | ClusterIP :8080            | vestigial — conductor is 100% AMQP                                   |

**GPU VM outbound (the only network path off this box)**

| from (GPU VM)     | via                              | to (old VM)                               | purpose                                          |
| ----------------- | -------------------------------- | ----------------------------------------- | ------------------------------------------------ |
| `localhost:5672`  | `tunnels/rabbitmq.sh` (`ssh -L`) | `:30673` → `rabbitmq-svc` (default ns)    | dev consumers: receive jobs / publish results    |
| `localhost:5673`  | `tunnels/rabbitmq-prod.sh`       | `:31673` → `rabbitmq-svc` (production ns) | prod consumers                                   |
| `localhost:18888` | `tunnels/proxy.sh`               | forward proxy → internet                  | NCBI BLAST, GCS (every consumer's result upload) |

The tunnels exist because the GPU VM's cloud-project firewall only allowlists ports that
already existed (`30072` passes, `30673`/`31673` do not) and we can't change it. Each
tunnel is its own `ssh -N` in a `while true; sleep 5` wrapper, key auth via
`~/.ssh/id_ed25519_oldvm`.

---

## Layout of one service dir

`~/proteng-gpu/apps[-prod]/<svc>/`

```
consumer.py         RabbitMQ-consumer entrypoint (has the reconnect fix, see below)
src/                service code (run_blast.py / run_mmseqs2.py / …)
pkg -> ~/proteng-gpu/app/pkg      absolute symlink, shared pkg.common across all services
venv/               per-service (name is "venv", not ".venv")
requirements.txt
run_forever.sh      respawn wrapper — self-contained env (see Supervision)
.env                loaded by consumer.py (load_dotenv); chmod 600
consumer.log
```

- **Hand-assembled, not a git checkout.** There is **no `git pull`** here and **no
  CI/CD**. A change to a `proteng-kubeflow` ML service must be copied onto the VM manually
  — onto **both** `apps/<svc>` and `apps-prod/<svc>` — and the files here have local edits
  that are not in the repo, so overwrite carefully (diff first).
- **Per-service venvs are mandatory** — real dependency conflicts:
  `blast`/`mmseqs2` need `pymongo==3.13.0`; `evotune`/`mutation` need `pymongo==4.10.1`;
  `fittop` pins `scikit-learn==1.2.2`; `evotune_ESM` needs `torch==2.10.0+cu128`
  (`2.11`'s `nvidia-nccl` pin doesn't publish — see `weekly-reports/20260828.md` §13 and
  the offline-pip recipe in the project notes).
- **`mmseqs2` extras**: the `mmseqs` binary is at `~/local/bin/mmseqs` (**not** on cron's
  PATH — the wrapper handles it). Each `mmseqs2` dir holds its own `uniprot_sprot.fasta`
  (~286 MB).
- Consumers **do not use MongoDB** — they only talk to RabbitMQ + GCS (+ NCBI for blast).
  `.env` needs `RABBITMQ_URL`, `PROJECT_ID`, `PRIVATE_KEY`, `PRIVATE_KEY_ID`,
  `CLIENT_EMAIL`, `CLIENT_ID`, `TOKEN_URI`. dev and prod use the **same** GCP service
  account (`cucpbioinfo`); only `RABBITMQ_URL` differs
  (`…@localhost:5672/` dev, `…@localhost:5673/` prod).

Each consumer declares a topic exchange `logs_topic`, an **`exclusive`** queue, one
binding key, and publishes results to the durable queue `job_status_event`
(`proteng-conductor` consumes that). `exclusive` means **only one consumer per queue** —
an in-cluster pod and a GPU VM consumer cannot both hold it, the loser loops on
`RESOURCE_LOCKED`.

| service           | queue               | binding key         |
| ----------------- | ------------------- | ------------------- |
| blast             | `blast_queue`       | `query.blast`       |
| mmseqs2           | `mmseqs2_queue`     | `query.mmseqs2`     |
| evotune           | `evotune_queue`     | `evotune.unirep`    |
| fittop            | `fittop_queue`      | `fittop.ridgecv`    |
| mutation          | `mutation_queue`    | `mutation.mutation` |
| evotune_ESM (dev) | `evotune_ESM_queue` | `evotune.ESM`       |

---

## Supervision

- **`run_forever.sh`** (one per service, identical file): `cd` to its dir, `export`
  `PATH="$HOME/local/bin:$PATH"` + `HTTP(S)_PROXY=http://localhost:18888` +
  `NO_PROXY=localhost,127.0.0.1`, then `while true; do venv/bin/python consumer.py; sleep 5; done`.
  **The env lives in this script, not the launching shell** — cron (`@reboot`, the
  watchdog) gives a minimal env, and without `PATH`/proxy here `mmseqs2` fails
  (`FileNotFoundError`) and blast + every GCS upload fail (`Network is unreachable`).
- **`consumer.py` reconnect fix** (`__main__`): recreates the asyncio event loop **and**
  the connection every `while True` iteration. `aio_pika`'s `RobustQueueIterator` has a
  hidden 60 s cap that silently raises `StopAsyncIteration` and kills the retry task; the
  old code then hung alive-but-idle. Job threads are deliberately **non-daemon**.
  Verified by a real >5 min tunnel-drop test (`20260904.md` §5).
- **Tunnels** — one `while true; ssh -N` wrapper each, in `~/proteng-gpu/tunnels/`.
  `autossh` is not installed; the watchdog covers a silently-dead tunnel.

### `~/proteng-gpu/bin/`

| script                         | what                                                                                                                                                                                                 |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `start-all.sh`                 | start the 3 tunnels + every `apps/*` and `apps-prod/*` supervisor. Idempotent (skips what's running).                                                                                                |
| `stop-all.sh [all\|dev\|prod]` | kill supervisors then their `consumer.py` children (matched by `/proc/<pid>/cwd`, since argv is the relative `./venv/bin/python consumer.py`). `prod` also stops the prod tunnel.                    |
| `status-all.sh`                | tunnels (process + socket), each consumer (supervisor pid, child pid, log age), last log line each.                                                                                                  |
| `healthcheck.sh`               | cron `*/5` — restart any dead supervisor, probe both AMQP sockets, and POST one line to `WEBHOOK_URL` (in `~/proteng-gpu/.env`) on a **state change**. Logs to `~/proteng-gpu/logs/healthcheck.log`. |

### crontab (`crontab -l`)

```
@reboot sleep 30 && ~/proteng-gpu/bin/start-all.sh >> ~/proteng-gpu/logs/boot.log 2>&1
*/5 * * * * ~/proteng-gpu/bin/healthcheck.sh
```

> During a **failback**, comment the `*/5` line first — otherwise the watchdog keeps
> respawning the prod supervisors into a `RESOURCE_LOCKED` loop.

---

## Relationship to `devops-k8s`

- `k8s/apps/rabbitmq/overlays/{dev,production}/kustomization.yaml` each add a `NodePort`
  patch to `rabbitmq-svc` (`30673` dev, `31673` prod) — **only** so the GPU VM tunnels can
  reach the in-cluster broker. Do not remove them (they've been wrongly reverted before —
  `20260904.md` §2).
- `k8s/apps/ml-pipeline/overlays/{dev,production}/kustomization.yaml` each pin the 5
  `ml-*` consumer Deployments to `replicas: 0` via a committed patch. **Load-bearing** — a
  live `kubectl scale` will not survive Argo self-heal, and a replica coming back fights
  the GPU VM consumer for the exclusive queue.
- Argo (`ml-pipeline-{dev,production}`) stays **Synced + Healthy** with the consumers at
  0; `ml-*-rest` run at 1.

---

## Deploying a change to a service here

There is no automation. For a code change to `<svc>`:

1. Copy the changed files onto the VM — `scp`, or `base64 -w0` on one side / `base64 -d`
   on the other for a single file; verify with `md5sum`. Terminal paste corrupts files.
2. Apply to **both** `~/proteng-gpu/apps/<svc>/` and `~/proteng-gpu/apps-prod/<svc>/`.
   These files have local edits not in the repo — `grep`/`diff` the target region first,
   don't blind-overwrite.
3. Restart just that service, dev + prod:
   ```sh
   for b in apps apps-prod; do
     d="$HOME/proteng-gpu/$b/<svc>"
     pkill -f "$d/run_forever.sh"
     for p in $(pgrep -f 'venv/bin/python .*consumer.py'); do
       [ "$(readlink /proc/$p/cwd)" = "$d" ] && kill "$p"
     done
   done
   ~/proteng-gpu/bin/start-all.sh
   ```
4. `~/proteng-gpu/bin/status-all.sh` + `tail ~/proteng-gpu/apps-prod/<svc>/consumer.log`.

A real deploy mechanism for this box is a proposal backlog item.

---

## Health check

```sh
~/proteng-gpu/bin/status-all.sh
cat ~/proteng-gpu/logs/healthcheck.log        # should be "all ok" every 5 min
ps aux | grep '[c]onsumer.py'                 # expect 6 dev + 5 prod
pwdx <pid>                                    # which service a consumer is
cat /proc/<pid>/environ | tr '\0' '\n' | grep -iE 'proxy|^PATH='
```

On the **old VM**: `microk8s kubectl -n production get pods | grep ml- | grep -v rest`
→ empty (consumers at 0); `microk8s kubectl -n argocd get applications.argoproj.io ml-pipeline-production`
→ Synced + Healthy.

---

## Failback (GPU VM → in-cluster, < 5 min)

1. GPU VM: comment the `*/5 healthcheck` cron line; `~/proteng-gpu/bin/stop-all.sh prod`;
   confirm `pgrep -af 'venv/bin/python .*consumer.py'` shows only the 6 dev ones.
2. `devops-k8s`: `git revert` the `replicas: 0` commit for the production overlay →
   `git push origin main`. Argo scales the 5 in-cluster consumers back to 1.
3. Old VM: `microk8s kubectl -n production get deploy | grep ml-` → back to 1/1, pods
   Running. Submit one prod job to confirm.
4. Leave the prod `NodePort 31673` and `tunnels/rabbitmq-prod.sh` — harmless, needed to
   re-cut-over later.

Same steps `dev`-flavoured to fail dev back.

---

## NCBI BLAST throughput test

`dev_tools/ncbi/ncbi_throughput_test.py` calls `NCBIWWW.qblast()` back-to-back N times and
records how long each takes — a real latency distribution for BLAST-via-NCBI (seen 4 min to
40+ min for the same query; see `20260904.md` §9). It imports nothing from the pipeline
(no RabbitMQ, no GCS), so the numbers are NCBI's latency only.

The script is already on the VM at `~/proteng-gpu/apps/blast/ncbi_throughput_test.py` (it
was never in a service dir on purpose — it's a helper). To re-transfer it, `base64 -w0` on
one side / `base64 -d` the other, verify `md5sum` (terminal paste corrupts it).

```sh
cd ~/proteng-gpu/apps/blast
export HTTP_PROXY=http://localhost:18888 HTTPS_PROXY=http://localhost:18888
export NCBI_EMAIL="you@example.com"
nohup ./venv/bin/python -u ncbi_throughput_test.py \
    --trials 15 --outfile ~/ncbi_throughput_$(date +%Y%m%d).csv \
    > ~/ncbi_throughput_$(date +%Y%m%d).log 2>&1 &

watch -n 30 cat ~/ncbi_throughput_*.csv
```

- Long — 15 trials × (4–40 min). `nohup … &` and walk away.
- **New `--outfile` each run** so you don't append to the old dataset.
- It shares the outbound path (`localhost:18888` → old VM proxy → NCBI, exiting on the old
  VM's IP) with the live `blast` consumers — dev _and_ prod. Run it when the `blast_queue`s
  are idle, or accept that it measures throughput under concurrent load (biopython
  `qblast` self-throttles per process; 2–3 concurrent streams from one IP can still hit
  NCBI's rate limit).
- Output CSV columns: `trial,start_utc,duration_s,status,hits,error`. stdout prints a line
  per trial then `min / max / mean / median` of the OK trials.

Backlog: `run_blast.py` should set `NCBIWWW.email` / `NCBIWWW.tool` (NCBI etiquette) — it
currently doesn't.

## Related

- [`dev_tools/ncbi/README.md`](../dev_tools/ncbi/README.md) — same test, full write-up.
- `manual-guides-2023/weekly-reports/20260904.md` §15 — the production cutover + the
  incident that produced most of the warnings above; §9 — the throughput results.
