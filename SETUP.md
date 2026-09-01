# Setup

Setup ทั้งระบบครั้งแรกดูที่ [Guidebook](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/README.md) ไฟล์นี้มีแค่รายละเอียดเฉพาะของ `proteng-kubeflow`

ไฟล์นี้เรื่อง **การพัฒนาบนเครื่อง local** deployment จริง (dev + production) รันบน GPU VM ดู
[docs/gpu-vm.md](./docs/gpu-vm.md)

## service ทั้ง 6 ตัว

ทั้ง 6 ตัวรูปแบบเดียวกันหมด: เป็น RabbitMQ consumer (`consumer.py`) ที่ bind queue แบบ
**exclusive** บน topic exchange `logs_topic` ด้วย routing key เดียว รัน job หนึ่งงานบน background
thread แล้ว publish ผลลัพธ์ไป durable queue `job_status_event` (ที่ `proteng-conductor` อ่าน)
ต่างกันแค่ job ทำอะไรและต้องใช้อะไรตอนรัน

| service | queue | routing key | pipeline stage | ต้องใช้ตอนรัน | รัน local ได้มั้ย |
| --- | --- | --- | --- | --- | --- |
| `blast` | `blast_queue` | `query.blast` | query | internet → NCBI BLAST (`NCBIWWW.qblast`) | ได้ |
| `mmseqs2` | `mmseqs2_queue` | `query.mmseqs2` | query | binary `mmseqs` บน `PATH` + `projects/mmseqs2/uniprot_sprot.fasta` (commit ไว้แล้ว) | ได้ หลังลง binary ตามข้างล่าง |
| `evotune` | `evotune_queue` | `evotune.unirep` | improvement | อ่าน artifact ของ query stage จาก GCS; `jax-unirep` (mlstm64 weights มากับ pip package) | ได้ ถ้ามี fake-gcs + patch `jax-unirep` ข้างล่าง |
| `fittop` | `fittop_queue` | `fittop.ridgecv` | improvement | อ่าน artifact ของ `evotune` จาก GCS; `jax-unirep` `get_reps` | ได้ เหมือนกัน |
| `mutation` | `mutation_queue` | `mutation.mutation` | improvement | อ่าน artifact ของ `evotune` + `fittop` จาก GCS; `jax-unirep` `get_reps` | ได้ เหมือนกัน |
| `evotune_ESM` | `evotune_ESM_queue` | `evotune.ESM` | improvement (POC ยังไม่ต่อเข้า conductor) | GCS + โหลด Hugging Face model (`AutoModelForMaskedLM.from_pretrained`) + `torch` (ควรมี GPU) | ไม่ครอบคลุมในนี้ |

input ของทุก stage คือ output ของ stage ก่อนหน้า ไม่มี trained model ที่ส่งมาจากข้างนอก ถ้า
credential GCP ว่าง จะรัน `blast` (ถึงก่อน upload) กับ `mmseqs2` (เหมือนกัน หลังลง binary) ได้
job จะตายด้วย `PRIVATE_KEY is not set` ตอนเรียก storage ครั้งแรก เพิ่ม **fake-gcs-server local**
(ขั้นที่ 2) แล้วทั้ง chain รันได้ — ดู "Full pipeline locally" ข้างล่าง
`dev_tools/rabbitmq/send_job.py` publish job query-stage หนึ่งงานสำหรับทดสอบเดี่ยว ๆ (ส่ง routing
key เช่น `query.mmseqs2`) ส่วน improvement stage ได้ message จาก conductor เท่านั้น

## Run locally

แต่ละ microservice ใน `projects/` (`blast`, `evotune`, `evotune_ESM`, `fittop`, `mmseqs2`,
`mutation`) setup แบบเดียวกัน แต่แต่ละตัวมี venv ของตัวเองและมีจุดจุกจิกของตัวเอง — ดูตารางข้างล่าง
ก่อนเริ่ม

1. **ไฟล์ env** — แต่ละ project มี `.env.local` ที่ชี้ broker **local** อยู่แล้ว
   (`RABBITMQ_URL=amqp://guest:guest@localhost:5672/`) พร้อม GCP creds ว่าง/dummy `consumer.py`
   โหลด `.env` (ไม่ใช่ `.env.local`) เลยต้อง copy:

   ```sh
   cd projects/<project-name>
   cp .env.local .env
   ```

   consumer ที่รัน local จะคุยกับ RabbitMQ ที่ **คุณ** รันเอง
   (`docker run -p 5672:5672 -p 15672:15672 rabbitmq:3-management`) แยกขาด ไม่แตะ queue ของ dev
   หรือ production ไม่มี job เข้าจนกว่าจะ publish เอง (`dev_tools/rabbitmq/send_job.py`)

   **ห้าม commit GCP service-account credential จริงลงไฟล์ใด ๆ ที่ git ติดตาม**

2. **GCS — creds ว่าง หรือใช้ emulator local** ทุก service อ่าน/เขียน job artifact ผ่าน
   `pkg/common/db.py` มีสองทาง:

   - **ปล่อย GCP block ว่าง** (default) job รันแล้ว raise `PRIVATE_KEY is not set` ตอนเรียก GCS
     ครั้งแรก — พอสำหรับทดสอบ RabbitMQ wiring และทุกอย่างก่อนถึง storage
   - **ชี้ไป [fake-gcs-server](https://github.com/fsouza/fake-gcs-server) local** ให้ job รันจบได้
     compose file พร้อม bucket ทั้ง 4 ของ pipeline อยู่ที่ `dev_tools/fake-gcs/`:

     ```sh
     docker compose -f dev_tools/fake-gcs/compose.yaml up -d
     # แล้วในแต่ละ projects/<svc>/.env ที่จะรันกับมัน:
     STORAGE_EMULATOR_HOST=http://localhost:4443
     ```

     consumer อ่าน `.env` **ครั้งเดียวตอน startup** — restart ตัวที่รันอยู่ `4443` เป็น default
     port ของ fake-gcs-server เอง library `google-cloud-storage` อ่าน `STORAGE_EMULATOR_HOST`
     เองแล้ว route request ทุกอันไปที่นั่นแทน `storage.googleapis.com` ดู
     `dev_tools/fake-gcs/README.md` เรื่องวิธี inspect/reset store และ "Full pipeline locally"
     ข้างล่างสำหรับการรัน end-to-end

   `STORAGE_EMULATOR_HOST` เป็น **opt-in และ local เท่านั้น** — commit ว่างไว้ในทุก `.env.example`
   และ consumer dev/production บน GPU VM **ห้ามตั้ง** ไม่งั้น library จะ route job จริงไป emulator
   local ที่ไม่มีอยู่แทนที่จะเป็น GCS

3. **สร้าง venv แล้วลง dependency** — version ที่ pin ไว้เป๊ะใน `requirements.txt` แต่ละไฟล์
   (`pandas==2.1.1`, `pydantic==2.5.2`, ฯลฯ) ไม่มี prebuilt wheel สำหรับ Python เวอร์ชันปัจจุบัน
   และ build จาก source ไม่ผ่าน (ต้องมี C/Rust compiler toolchain ที่เราไม่มี) ลงแบบ **ไม่ pin**
   แล้วให้ pip resolve version ใหม่ที่เข้ากันได้:

   ```sh
   python -m venv .venv
   source .venv/Scripts/activate   # Windows Git Bash; macOS/Linux: source .venv/bin/activate
   sed 's/[=<>].*$//' requirements.txt > /tmp/req.txt   # ตัด version pin
   pip install -r /tmp/req.txt -r ../../pkg/common/requirements.txt
   ```

   `requirements.txt` บางไฟล์ save เป็น UTF-16 (ไม่ใช่ ASCII) — ถ้า `sed`/`grep` พังหรือได้ขยะ
   เช็คด้วย `file requirements.txt` ก่อน แล้ว decode ด้วย `iconv -f UTF-16LE -t UTF-8` ก่อน pipe
   เข้า `sed`

   **จุดจุกจิกต่อ project** (เพิ่มจากด้านบน):

   | Project | ขั้นตอนเพิ่ม |
   | --- | --- |
   | `blast` | ไม่มี |
   | `mmseqs2` | (1) เอา `bson` ออกจาก install — เป็น package legacy/ไม่ maintain build ไม่ผ่านบน Python ใหม่ และไม่จำเป็น: `pymongo` ให้ `from bson import ObjectId` อยู่แล้ว (2) ต้องมี binary `mmseqs` บน `PATH` — ดูข้างล่าง |
   | `evotune`, `evotune_ESM`, `fittop`, `mutation` | เพิ่ม `pip install "setuptools<81"` — พวกนี้ใช้ `jax-unirep` ซึ่ง `import pkg_resources` (ส่วนหนึ่งของ setuptools) setuptools ≥81 เอา module นั้นออกแล้ว |
   | `evotune_ESM` | install หนักสุด (`torch`, `transformers`, `datasets`, `optuna`) — หลายนาที |

   **`mmseqs2` — binary `mmseqs`** `run_mmseqs2.py` shell out ไป `mmseqs easy-search` เลย binary
   ต้องอยู่บน `PATH` (ไม่มี path override ในโค้ด) search database
   (`projects/mmseqs2/uniprot_sprot.fasta`, ~286 MB Swiss-Prot) commit ไว้ใน repo แล้ว

   - **Windows**: โหลด
     <https://github.com/soedinglab/MMseqs2/releases/latest/download/mmseqs-win64.zip>
     (mirror `mmseqs.com/latest/` มีแค่ build Linux/macOS) แล้วแตกไฟล์ เช่นไปที่
     `C:\Users\<you>\mmseqs` archive มีแค่ `bin\mmseqs.exe` + `bin\busybox.exe`;
     `mmseqs easy-search` เป็น shell workflow ที่ต้องใช้ tool แบบ GNU เลยต้อง install BusyBox
     applet ครั้งเดียว:

     ```powershell
     C:\Users\<you>\mmseqs\bin\busybox.exe --install C:\Users\<you>\mmseqs\bin
     ```

     แล้วเพิ่ม **`...\mmseqs\bin`** (ไม่ใช่โฟลเดอร์ที่มี `mmseqs.bat`) เข้า user `PATH` —
     `run_mmseqs2.py` เรียก `subprocess.run(["mmseqs", ...])` โดยไม่ผ่าน shell และ Windows
     resolve `mmseqs.exe` ได้แต่ `mmseqs.bat` ไม่ได้:

     ```powershell
     [Environment]::SetEnvironmentVariable("Path",
       [Environment]::GetEnvironmentVariable("Path","User") + ";C:\Users\<you>\mmseqs\bin", "User")
     ```

   - **macOS**: `brew install mmseqs2` หรือ `mmseqs-osx-universal.tar.gz` จากหน้า releases
     **Linux**: `mmseqs-linux-*.tar.gz` แบบ static (เลือก `avx2` บน CPU ใหม่, `sse41`/`sse2` ถ้าเก่า)
     — เอา `mmseqs` ใส่ `PATH`
   - เช็คใน terminal **ใหม่** (ปิด window `./run.sh` ด้วย มันถือ `PATH` เก่า):
     `mmseqs version` ต้องพิมพ์ commit hash

   ถ้าไม่มี job `mmseqs2` จะ fail ทันทีด้วย `FileNotFoundError: ... 'mmseqs'` ถ้าไม่ต้องรัน
   `mmseqs2` local ก็ข้าม service นี้ได้ มันรันบน GPU VM ได้ปกติ

4. **รัน microservice** — แต่ละ project มี `run.sh` ที่ copy `.env.local` → `.env` (รันครั้งแรก
   เท่านั้น) แล้วเรียก `python` ของ venv ตรง ๆ ไม่ต้อง `source .venv/Scripts/activate` ก่อน จาก
   root ของ repo:

   ```sh
   ./run.sh blast          # service เดียว (หรือ: cd projects/blast && ./run.sh)
   ./run.sh all            # ทุก service แต่ละตัว background, Ctrl-C หยุดหมด
   ```

   (รัน `consumer.py` ซึ่งเป็น entrypoint ที่ใช้จริงตอนนี้ `microservice.py` ในแต่ละ project เป็น
   FastAPI entrypoint เก่าที่ไม่ได้ต่อแล้ว ถ้าจะรันมือ: `source .venv/Scripts/activate` แล้ว
   `python consumer.py`)

   เสร็จเมื่อ log ขึ้น `Connecting to RabbitMQ` → `Connected to RabbitMQ` → `Consuming messages`
   ไม่ crash ไม่มี HTTP port เป็น consumer เปล่า ๆ รันครั้งแรกอาจ 20-30 วิ ก่อนมีอะไรขึ้น (import
   `jax`/ML library ช้า) ปกติ ไม่ใช่ค้าง

   แต่ละ microservice เป็น process ที่ block ตัวเองมี venv ของตัวเอง `./run.sh all` background
   ทุกตัว (ข้าม `evotune_ESM` — มันดึง `torch`; `RUN_ESM=1 ./run.sh all` ถ้าจะเอาด้วย) แต่ปกติ
   ต้องการแค่ตัวที่เกี่ยวกับที่กำลังทดสอบ และทุก venv ต้องมีอยู่ก่อน

## Full pipeline locally

รัน `blast|mmseqs2 → evotune → fittop → mutation` จนขึ้น **Completed** บนเครื่องเดียว โดยมี
`proteng-conductor` จริงเป็นตัวขับ แต่ละ stage ส่ง artifact ให้ stage ถัดไปผ่าน GCS bucket input
ของทุก stage คือ output ของ stage ก่อนหน้า:

```
query (blast|mmseqs2) --> similar_protein --> evotune --> unirep --> fittop --> ridgecv --> mutation --> mutation
```

`evotune_ESM` ไม่อยู่ใน chain นี้ — เป็น POC ไม่มี stage ใน conductor

1. **Infra**: RabbitMQ + Mongo (ดูขั้นที่ 1) + GCS emulator:

   ```sh
   docker compose -f dev_tools/fake-gcs/compose.yaml up -d
   curl -s localhost:4443/storage/v1/b        # list similar_protein, unirep, ridgecv, mutation
   ```

2. **Patch `jax-unirep`** ให้ `evotune` / `fittop` / `mutation` (JAX ใหม่เอา kwarg
   `jax.numpy.clip(a_min=...)` ที่พวกนี้ยังใช้ออกแล้ว):

   ```sh
   python dev_tools/patches/fix_jax_unirep.py
   ```

   รันซ้ำทุกครั้งที่ rebuild venv พวกนั้น (ดู `dev_tools/patches/README.md`)

3. **App service** — จากแต่ละ repo ด้วย `.env.local` (default เป็น local อยู่แล้ว — ดู `SETUP.md`
   ของแต่ละ repo):

   ```sh
   # proteng-user-mgmt, proteng-conductor, proteng-bff  (Git Bash, terminal ละอัน)
   ./run.sh
   # protengplus-frontend
   npm run dev
   ```

4. **Consumer** — ตั้ง `STORAGE_EMULATOR_HOST=http://localhost:4443` ในแต่ละ `projects/<svc>/.env`
   (`blast`, `mmseqs2`, `evotune`, `fittop`, `mutation`) แล้ว:

   ```sh
   ./run.sh all        # จาก shell ที่มี mmseqs บน PATH; evotune_ESM ถูกข้าม
   ```

   ทั้ง 5 ตัวขึ้น `Consuming messages`

5. **Submit** — ในหน้าเว็บ: สมัคร user สร้าง job แบบ **auto** เลือก query tool submit ดู log ของ
   consumer ไล่ `mmseqs2 … completed` → `evotune … completed` → `fittop … completed` →
   `mutation … completed`; job ในหน้าเว็บเปลี่ยนเป็น **Completed** เช็ค artifact สุดท้าย:

   ```sh
   curl -s localhost:4443/storage/v1/b/mutation/o
   ```

ค่า job-config ที่ frontend ส่งมาอาจดูแปลก (เช่น `e: 70`, `min_seq_id: 70`) เป็น bug typing ของ
frontend (field `e` type เป็น `percent` ใน `createJobConfig.ts`) ไม่ใช่ setup ผิด และไม่ block
การรัน

## Format & lint

`black` autofix ตอน commit/push, `ruff` autofix ปัญหาส่วนใหญ่ รันมือทั้ง repo:

```sh
black .
ruff check --fix .
```

`black --check` + `ruff check` (ไม่ autofix) รันใน CI (`.github/workflows/test-build-dev.yaml`)
ทุก push CI ลง `black`/`ruff` version เดียวกับ `.pre-commit-config.yaml` เป๊ะ — bump ตัวไหน bump
ทั้งคู่ `ruff.toml` ตั้ง `select` ชัดเจนกันกฎเลื่อนตาม version รายละเอียด hook ดู
[CONTRIBUTING.md](./CONTRIBUTING.md)

hook `git commit` / `git push` เรียก `pre-commit` ด้วย full path เลยทำงานแม้ `pre-commit` ไม่อยู่
บน `PATH` แต่รันมือเองอาจไม่ได้: `pip install --user` (กับ conda-base pip บน Windows) วาง
executable ไว้นอก `PATH` ถ้า `pre-commit` "not recognized" เรียกตรง ๆ เช่น
`python -m pre_commit run --all-files` หรือเพิ่มโฟลเดอร์ `Scripts` เข้า `PATH`
