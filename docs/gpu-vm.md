# GPU VM — runbook ของ ML pipeline

`ml-pipeline` ทั้งหมด (`blast`, `mmseqs2`, `evotune`, `evotune_ESM`, `fittop`, `mutation`)
รัน **นอก cluster** บน GPU VM `isel-5090` / `161.200.92.6` (RTX 5090) ทั้งสอง environment อยู่ที่นี่:

- **dev** — `~/proteng-gpu/apps/<svc>/` — 6 service (รวม `evotune_ESM`)
- **production** — `~/proteng-gpu/apps-prod/<svc>/` — 5 service (ไม่มี `evotune_ESM`)

`ml-*` consumer Deployment ใน cluster บน VM เก่าถูกตรึง `replicas: 0` ใน git (ดู
[Relationship to devops-k8s](#relationship-to-devops-k8s)) ส่วน `ml-*-rest` FastAPI Deployment
เป็น dead weight (ไม่มีอะไร route ไปหา) ปล่อยไว้

เครื่องนี้อยู่ใน **cloud project ที่เราไม่ได้คุม**: ไม่มี `sudo`, ไม่มี Docker, และเปลี่ยน firewall
ไม่ได้ (allowlist เฉพาะ NodePort ที่มีอยู่เดิม) ทุกอย่างข้างล่างทำงานภายในข้อจำกัดนี้

> `SETUP.md` ที่ root ของ repo ครอบคลุมการรัน service **บนเครื่อง local** ไฟล์นี้เรื่อง deployment
> บน GPU VM

---

## อะไรรันที่ไหน

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

**service → host → port**

| service                                               | host                  | dev port                                  | prod port                  | หมายเหตุ                                                                |
| ----------------------------------------------------- | --------------------- | ----------------------------------------- | -------------------------- | ----------------------------------------------------------------------- |
| nginx-proxy                                           | old VM (host Docker)  | :80 → redirect 443, :443                  | เหมือนกัน                  | TLS term, route ตาม hostname                                            |
| protengplus-web (frontend)                            | old VM MicroK8s       | NodePort 30001                            | NodePort 31001             |                                                                         |
| proteng-bff                                           | old VM MicroK8s       | NodePort 30080                            | NodePort 31080             | back `doc.protengplus.com` ด้วย                                         |
| proteng-user-mgmt                                     | old VM MicroK8s       | NodePort 30081                            | NodePort 31081             |                                                                         |
| proteng-conductor                                     | old VM MicroK8s       | NodePort 30082                            | NodePort 31082             | publish job ไป RabbitMQ ต่อ stage                                       |
| RabbitMQ AMQP (`rabbitmq-svc`)                        | old VM MicroK8s       | **NodePort 30673**                        | **NodePort 31673**         | overlay เพิ่มให้ _เฉพาะ_ tunnel ของ GPU VM — อย่าเอาออก                 |
| RabbitMQ mgmt UI                                      | old VM MicroK8s       | NodePort 30072                            | NodePort 31072             |                                                                         |
| Argo CD                                               | old VM MicroK8s       | NodePort 30098 (`argocd.protengplus.com`) | —                          |                                                                         |
| MongoDB                                               | old VM (host Docker)  | :27017                                    | container เดียวกัน         | ไม่อยู่ใน k8s; consumer ที่นี่ **ไม่แตะ** (conductor เป็นเจ้าของ Mongo) |
| `ml-{blast,mmseqs2,evotune,fittop,mutation}` consumer | **GPU VM**            | `~/proteng-gpu/apps/`                     | `~/proteng-gpu/apps-prod/` | ไม่มี inbound port; outbound AMQP + HTTPS เท่านั้น                      |
| `evotune_ESM`                                         | GPU VM (dev เท่านั้น) | `~/proteng-gpu/apps/evotune_ESM`          | —                          | ไม่มี k8s manifest ไม่มี stage `esm` ใน conductor — POC                 |
| `ml-*` consumer Deployment                            | old VM MicroK8s       | **replicas 0**                            | **replicas 0**             | served จาก GPU VM                                                       |
| `ml-*-rest` (5 FastAPI)                               | old VM MicroK8s       | ClusterIP :8080                           | ClusterIP :8080            | vestigial — conductor เป็น AMQP 100%                                    |

**GPU VM outbound (ทางเดียวที่ออกจากเครื่องนี้ได้)**

| จาก (GPU VM)      | ผ่าน                             | ไป (old VM)                               | เพื่ออะไร                                  |
| ----------------- | -------------------------------- | ----------------------------------------- | ------------------------------------------ |
| `localhost:5672`  | `tunnels/rabbitmq.sh` (`ssh -L`) | `:30673` → `rabbitmq-svc` (default ns)    | dev consumer: รับ job / publish ผล         |
| `localhost:5673`  | `tunnels/rabbitmq-prod.sh`       | `:31673` → `rabbitmq-svc` (production ns) | prod consumer                              |
| `localhost:18888` | `tunnels/proxy.sh`               | forward proxy → internet                  | NCBI BLAST, GCS (upload ผลของทุก consumer) |

tunnel มีเพราะ firewall ของ cloud project ฝั่ง GPU VM allowlist เฉพาะ port ที่มีอยู่เดิม (`30072`
ผ่าน `30673`/`31673` ไม่ผ่าน) และเราเปลี่ยนไม่ได้ tunnel แต่ละเส้นเป็น `ssh -N` ของตัวเองใน wrapper
`while true; sleep 5` key auth ผ่าน `~/.ssh/id_ed25519_oldvm`

---

## Layout ของ service dir หนึ่งตัว

`~/proteng-gpu/apps[-prod]/<svc>/`

```
consumer.py         entrypoint ของ RabbitMQ consumer (มี reconnect fix ดูข้างล่าง)
src/                โค้ด service (run_blast.py / run_mmseqs2.py / …)
pkg -> ~/proteng-gpu/app/pkg      absolute symlink, shared pkg.common ข้ามทุก service
venv/               ต่อ service (ชื่อ "venv" ไม่ใช่ ".venv")
requirements.txt
run_forever.sh      respawn wrapper — ถือ env เอง (ดู Supervision)
.env                โหลดโดย consumer.py (load_dotenv); chmod 600
consumer.log
```

- **ประกอบมือ ไม่ใช่ git checkout** ที่นี่ **ไม่มี `git pull`** และ **ไม่มี CI/CD** การแก้ ML
  service ใน `proteng-kubeflow` ต้อง copy ขึ้น VM เอง — ลง **ทั้ง** `apps/<svc>` และ
  `apps-prod/<svc>` — และไฟล์ที่นี่มี local edit ที่ไม่อยู่ใน repo overwrite ระวัง (diff ก่อน)
- **venv ต่อ service บังคับ** — dependency ชนกันจริง: `blast`/`mmseqs2` ต้องการ
  `pymongo==3.13.0`; `evotune`/`mutation` ต้องการ `pymongo==4.10.1`; `fittop` pin
  `scikit-learn==1.2.2`; `evotune_ESM` ต้องการ `torch==2.10.0+cu128` (`2.11`'s `nvidia-nccl`
  pin ไม่ publish — ดู `/resources-2026/weekly-reports/20260828.md` §13 และ recipe offline-pip ใน project notes)
- **`mmseqs2` เพิ่มเติม**: binary `mmseqs` อยู่ที่ `~/local/bin/mmseqs` (**ไม่**อยู่บน PATH ของ
  cron — wrapper จัดการ) แต่ละ `mmseqs2` dir ถือ `uniprot_sprot.fasta` ของตัวเอง (~286 MB)
- consumer **ไม่ใช้ MongoDB** — คุยแค่ RabbitMQ + GCS (+ NCBI สำหรับ blast) `.env` ต้องมี
  `RABBITMQ_URL`, `PROJECT_ID`, `PRIVATE_KEY`, `PRIVATE_KEY_ID`, `CLIENT_EMAIL`, `CLIENT_ID`,
  `TOKEN_URI` dev กับ prod ใช้ GCP service account **เดียวกัน** (`cucpbioinfo`) ต่างกันแค่
  `RABBITMQ_URL` (`…@localhost:5672/` dev, `…@localhost:5673/` prod)

consumer แต่ละตัว declare topic exchange `logs_topic`, queue แบบ **`exclusive`**, binding key
หนึ่งอัน และ publish ผลไป durable queue `job_status_event` (`proteng-conductor` consume อันนั้น)
`exclusive` แปลว่า **มี consumer ได้ตัวเดียวต่อ queue** — pod ใน cluster กับ consumer บน GPU VM
ถือพร้อมกันไม่ได้ ตัวที่แพ้จะวน `RESOURCE_LOCKED`

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

- **`run_forever.sh`** (ตัวเดียวต่อ service ไฟล์เหมือนกันหมด): `cd` เข้า dir ของมัน `export`
  `PATH="$HOME/local/bin:$PATH"` + `HTTP(S)_PROXY=http://localhost:18888` +
  `NO_PROXY=localhost,127.0.0.1` แล้ว `while true; do venv/bin/python consumer.py; sleep 5; done`
  **env อยู่ใน script นี้ ไม่ใช่ shell ที่สตาร์ท** — cron (`@reboot`, watchdog) ให้ env มินิมอล
  ถ้าไม่มี `PATH`/proxy ที่นี่ `mmseqs2` จะ fail (`FileNotFoundError`) และ blast + GCS upload
  ทุกอันจะ fail (`Network is unreachable`)
- **`consumer.py` reconnect fix** (`__main__`): สร้าง asyncio event loop **และ** connection ใหม่
  ทุกรอบ `while True` `RobustQueueIterator` ของ `aio_pika` มี cap ซ่อน 60 วิ ที่ raise
  `StopAsyncIteration` เงียบ ๆ แล้วฆ่า retry task ทำให้โค้ดเดิมค้าง alive-but-idle job thread
  จงใจเป็น **non-daemon** ยืนยันด้วยการ test tunnel-drop จริง >5 นาที (`20260904.md` §5)
- **Tunnel** — wrapper `while true; ssh -N` ตัวเดียวต่อเส้น อยู่ใน `~/proteng-gpu/tunnels/`
  ไม่ได้ลง `autossh` watchdog ครอบ tunnel ที่ตายเงียบ

### `~/proteng-gpu/bin/`

| script                         | ทำอะไร                                                                                                                                                                                              |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `start-all.sh`                 | start tunnel 3 เส้น + supervisor ของทุก `apps/*` และ `apps-prod/*` idempotent (ข้ามตัวที่รันอยู่)                                                                                                   |
| `stop-all.sh [all\|dev\|prod]` | kill supervisor แล้วตามด้วย child `consumer.py` (match ด้วย `/proc/<pid>/cwd` เพราะ argv เป็น relative `./venv/bin/python consumer.py`) `prod` หยุด tunnel prod ด้วย                                |
| `status-all.sh`                | tunnel (process + socket), consumer แต่ละตัว (supervisor pid, child pid, log age), บรรทัด log ล่าสุด                                                                                                |
| `healthcheck.sh`               | cron `*/5` — restart supervisor ที่ตาย, probe AMQP socket ทั้งสอง, และ POST หนึ่งบรรทัดไป `WEBHOOK_URL` (ใน `~/proteng-gpu/.env`) ตอน **state เปลี่ยน** log ไป `~/proteng-gpu/logs/healthcheck.log` |

### crontab (`crontab -l`)

```
@reboot sleep 30 && ~/proteng-gpu/bin/start-all.sh >> ~/proteng-gpu/logs/boot.log 2>&1
*/5 * * * * ~/proteng-gpu/bin/healthcheck.sh
```

> ตอน **failback** comment บรรทัด `*/5` ก่อน ไม่งั้น watchdog จะ respawn supervisor prod วนเข้า
> loop `RESOURCE_LOCKED`

---

## Relationship to devops-k8s

- `k8s/apps/rabbitmq/overlays/{dev,production}/kustomization.yaml` แต่ละอันเพิ่ม patch
  `NodePort` ให้ `rabbitmq-svc` (`30673` dev, `31673` prod) — **เฉพาะ** เพื่อให้ tunnel ของ
  GPU VM ต่อ broker ใน cluster ได้ อย่าเอาออก (เคยถูก revert ผิดมาแล้ว — `20260904.md` §2)
- `k8s/apps/ml-pipeline/overlays/{dev,production}/kustomization.yaml` แต่ละอันตรึง `ml-*`
  consumer Deployment 5 ตัวเป็น `replicas: 0` ด้วย patch ที่ commit ไว้ **สำคัญ** — live
  `kubectl scale` ไม่รอด Argo self-heal และ replica ที่กลับมาจะแย่ง exclusive queue กับ
  consumer บน GPU VM
- Argo (`ml-pipeline-{dev,production}`) ยัง **Synced + Healthy** โดย consumer อยู่ที่ 0;
  `ml-*-rest` รันที่ 1

---

## Deploy การเปลี่ยนแปลงของ service ที่นี่

ไม่มี automation สำหรับ code change ของ `<svc>`:

1. copy ไฟล์ที่แก้ขึ้น VM — `scp` หรือ `base64 -w0` ฝั่งนึง / `base64 -d` อีกฝั่งสำหรับไฟล์เดียว
   verify ด้วย `md5sum` การ paste ใน terminal ทำไฟล์เสีย
2. ลงทั้ง `~/proteng-gpu/apps/<svc>/` และ `~/proteng-gpu/apps-prod/<svc>/` ไฟล์พวกนี้มี local
   edit ที่ไม่อยู่ใน repo — `grep`/`diff` บริเวณเป้าหมายก่อน อย่า overwrite มั่ว
3. restart เฉพาะ service นั้น ทั้ง dev + prod:

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

4. `~/proteng-gpu/bin/status-all.sh` + `tail ~/proteng-gpu/apps-prod/<svc>/consumer.log`

deploy mechanism จริงสำหรับเครื่องนี้เป็น proposal backlog

---

## Health check

```sh
~/proteng-gpu/bin/status-all.sh
cat ~/proteng-gpu/logs/healthcheck.log        # ควรเป็น "all ok" ทุก 5 นาที
ps aux | grep '[c]onsumer.py'                 # คาด 6 dev + 5 prod
pwdx <pid>                                    # consumer ตัวนี้คือ service ไหน
cat /proc/<pid>/environ | tr '\0' '\n' | grep -iE 'proxy|^PATH='
```

บน **VM เก่า**: `microk8s kubectl -n production get pods | grep ml- | grep -v rest`
→ ว่าง (consumer อยู่ที่ 0); `microk8s kubectl -n argocd get applications.argoproj.io ml-pipeline-production`
→ Synced + Healthy

---

## Failback (GPU VM → in-cluster, < 5 นาที)

1. GPU VM: comment บรรทัด cron `*/5 healthcheck`; `~/proteng-gpu/bin/stop-all.sh prod`;
   ยืนยัน `pgrep -af 'venv/bin/python .*consumer.py'` เห็นแค่ 6 ตัว dev
2. `devops-k8s`: `git revert` commit `replicas: 0` ของ production overlay → `git push origin main`
   Argo scale consumer ใน cluster 5 ตัวกลับเป็น 1
3. VM เก่า: `microk8s kubectl -n production get deploy | grep ml-` → กลับเป็น 1/1 pod Running
   submit prod job หนึ่งงานยืนยัน
4. ปล่อย prod `NodePort 31673` กับ `tunnels/rabbitmq-prod.sh` ไว้ — ไม่มีผลเสีย ต้องใช้ตอน
   re-cutover ทีหลัง

fail dev กลับ ทำ step เดียวกันแบบ `dev`

---

## NCBI BLAST throughput test

helper วัด latency ของ BLAST-via-NCBI ล้วน ๆ (`NCBIWWW.qblast()` ไม่แตะ pipeline) — query เดียวกัน
**วิธีรันอยู่ที่ [`dev_tools/ncbi/README.md`](../dev_tools/ncbi/README.md)**

เฉพาะบริบท GPU VM:

- script อยู่บน VM แล้วที่ `~/proteng-gpu/apps/blast/ncbi_throughput_test.py` (helper — จงใจไม่ไว้ใน service dir); transfer ใหม่ใช้ `scp` หรือ `base64` + เทียบ `md5sum` (paste ผ่าน terminal ไฟล์เพี้ยน)
- ยิงออก path เดียวกับ `blast` consumer (`localhost:18888` → proxy VM เก่า → NCBI ที่ IP VM เก่า) — **อย่ารันพร้อม prod blast job** (2–3 stream จาก IP เดียวชน rate limit NCBI)

## Related

- [`dev_tools/ncbi/README.md`](../dev_tools/ncbi/README.md) — วิธีรัน throughput test
- [`manual-guides-2023/resources-2026/notes/ncbi-usage.md`](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/resources-2026/notes/ncbi-usage.md) — ระบบแตะ NCBI ตรงไหน, พารามิเตอร์, rate limit, ผล throughput
- `manual-guides-2023/resources-2026/weekly-reports/20260904.md` §15 — production cutover + incident; §9 — ผล throughput
