# proteng-kubeflow

repo นี้เก็บ ML service ทุกตัวของ ProtEngPlus แต่ละ service เป็น RabbitMQ consumer ที่รับงานของ stage หนึ่งจาก `proteng-conductor` อ่านและเขียน artifact ใน Google Cloud Storage แล้วส่งผลกลับผ่าน queue `job_status_event` ภาพรวมของทั้งระบบอยู่ที่ [manual-guides-2023](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/reference/architecture.md)

ชื่อ repo มาจากแผนแรกของรุ่นก่อนที่จะใช้ Kubeflow ทำ pipeline แต่สุดท้ายไม่ได้ใช้ ระบบตอนนี้ไม่มีส่วนไหนใช้ Kubeflow

repo นี้เป็น public ห้ามใส่รายละเอียดของเครื่องที่ใช้ deploy เช่น IP, port ของ SSH, path บนเครื่อง หรือ runbook ข้อมูลเหล่านั้นอยู่ใน manual-guides-2023 และ devops-infra ซึ่งเป็น private

## service

| service | queue | routing key | stage | ต้องใช้ตอนรัน |
| --- | --- | --- | --- | --- |
| `blast` | `blast_queue` | `query.blast` | query | อินเทอร์เน็ตเพื่อเรียก NCBI BLAST ผ่าน `NCBIWWW.qblast` |
| `mmseqs2` | `mmseqs2_queue` | `query.mmseqs2` | query | โปรแกรม `mmseqs` ใน `PATH` และ `projects/mmseqs2/uniprot_sprot.fasta` ซึ่งเก็บด้วย Git LFS |
| `evotune` | `evotune_queue` | `evotune.unirep` | improvement | artifact ของ stage query และ `jax-unirep` |
| `fittop` | `fittop_queue` | `fittop.ridgecv` | improvement | artifact ของ `evotune` และ `jax-unirep` |
| `mutation` | `mutation_queue` | `mutation.mutation` | improvement | artifact ของ `evotune` และ `fittop` และ `jax-unirep` |
| `evotune_ESM` | `evotune_ESM_queue` | `evotune.ESM` | proof of concept ยังไม่ได้ต่อเข้า conductor | model จาก Hugging Face และ `torch` ควรมี GPU |

ทุก service bind queue แบบ exclusive เข้ากับ topic exchange `logs_topic` ด้วย routing key ของตัวเอง และรันงานทีละงานใน background thread artifact ส่งต่อกันผ่าน bucket ดังนี้

```text
query (blast หรือ mmseqs2) -> similar_protein -> evotune -> unirep -> fittop -> ridgecv -> mutation -> mutation
```

## เริ่มใช้

ถ้ายังไม่เคยตั้งเครื่องสำหรับ ProtEngPlus ให้ทำตาม [tutorials/01-local-setup.md](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/tutorials/01-local-setup.md) ของ hub ซึ่งตั้งทุก repo พร้อมกัน ถ้าจะตั้งเฉพาะ repo นี้ ให้รันใน Git Bash

```sh
make setup
make env-local-gcs
make -C ../manual-guides-2023 infra-up
make run SVC=mmseqs2
```

- `make setup` ติดตั้ง git hook, สร้าง `projects/<svc>/.env` จาก `.env.example` (ไม่ทับไฟล์ที่มีอยู่แล้ว) และสร้าง venv ของ service ทั้ง 5 ตัว ครั้งแรกใช้เวลาประมาณ 10 นาที
- `make env-local-gcs` ชี้ทุก service ไปที่ fake-gcs ในเครื่อง จะได้รันจนจบได้โดยไม่ต้องมี credential ของ GCP
- `make run SVC=<svc>` ผ่านเมื่อ log ขึ้น `Connecting to RabbitMQ`, `Connected to RabbitMQ` แล้ว `Consuming messages` ครั้งแรกอาจเงียบไป 20 ถึง 30 วินาทีเพราะ import library ของ ML ช้า

ต้องมี Python 3.11 ขึ้นไป, Docker และ `pip install pre-commit black==25.1.0 ruff==0.16.5` ส่วน mmseqs2 ต้องมีโปรแกรม `mmseqs` ใน `PATH` วิธีติดตั้งบน Windows อยู่ใน tutorial ข้างบน

## คำสั่ง

พิมพ์ `make` เพื่อดูคำสั่งทั้งหมด

| คำสั่ง | ทำอะไร |
| --- | --- |
| `make setup` | ติดตั้ง hook, สร้าง `.env` และ venv ของ service ทั้ง 5 ตัว รันซ้ำได้ |
| `make env` และ `make env-local-gcs` | สร้าง `.env` จาก `.env.example` และตั้ง `STORAGE_EMULATOR_HOST` ให้ชี้ fake-gcs |
| `make venv SVC=<svc>` และ `make venvs` | สร้างหรืออัปเดต venv ของ service เดียวหรือทั้ง 5 ตัว ใส่ `ESM=1` เพื่อรวม `evotune_ESM` |
| `make patch-jax` | ใส่ patch ของ `jax-unirep` ซ้ำในทุก venv ที่มีอยู่ |
| `make run SVC=<svc>` และ `make run-all` | รัน service เดียว หรือทุกตัวพร้อมกันแล้วกด Ctrl-C เพื่อหยุดทั้งหมด (`RUN_ESM=1` เพื่อรวม `evotune_ESM`) |
| `make gcs-up` และ `make gcs-down` | เปิดหรือปิด fake-gcs ถ้าเปิดผ่าน `infra-up` ของ hub แล้วไม่ต้องใช้ |
| `make send-job KEY=query.mmseqs2` | ส่งงาน query หนึ่งงานเข้า RabbitMQ ในเครื่อง เพื่อทดสอบ service เดียวโดยไม่ต้องมี conductor |
| `make check` | black, ruff และ `bash -n` เหมือนกับ CI |
| `make fmt` | จัด format ด้วย black และแก้ด้วย ruff |
| `make docker-build SVC=<svc>` | build image ของ service ในเครื่อง |
| `make gpu-status` และ `make gpu-drift` | ดูสถานะและเทียบโค้ดกับเครื่องที่ใช้ deploy ต้องมีสิทธิ์เข้าเครื่องก่อน วิธีใช้อยู่ใน hub |

## Config

แต่ละ service อ่าน `projects/<svc>/.env` ครั้งเดียวตอนเริ่ม ถ้าแก้ต้อง restart

| ตัวแปร | ค่าตอนรัน local | ใช้ทำอะไร |
| --- | --- | --- |
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/` (มาจาก `.env.example`) | broker ที่รับงาน |
| `STORAGE_EMULATOR_HOST` | `http://localhost:4443` (ตั้งด้วย `make env-local-gcs`) | ส่ง request ของ GCS ไปที่ fake-gcs ใช้เฉพาะในเครื่องเท่านั้น |
| `PROJECT_ID`, `PRIVATE_KEY_ID`, `PRIVATE_KEY`, `CLIENT_EMAIL`, `CLIENT_ID`, `TOKEN_URI` | ว่างไว้ได้เมื่อใช้ fake-gcs | service account ของ GCP ที่ใช้อ่านและเขียน artifact |
| `DEBUG` | ว่าง | ตั้งเป็น `true` เพื่อเปิด log ระดับ debug |

ห้ามตั้ง `STORAGE_EMULATOR_HOST` ในเครื่องที่รันงานจริง เพราะ library ของ GCS จะส่ง job จริงไปยัง emulator ที่ไม่มีอยู่ และห้าม commit ค่าของ service account ลงไฟล์ใดใน repo ค่าของ dev และ production อยู่ในเครื่องที่ใช้ deploy ไม่ได้อยู่ใน repo นี้

## โครงสร้างโค้ด

```text
pkg/common/            โค้ดที่ทุก service ใช้ร่วมกัน: RabbitMQ (mq.py, publisher.py), GCS (db.py), logger
projects/<svc>/
  consumer.py          entrypoint ที่ใช้จริง: ต่อ RabbitMQ แล้วรับงาน
  microservice.py      entrypoint แบบ FastAPI รุ่นแรก ไม่ได้ใช้แล้ว
  src/service/         logic ของ service
  src/const.py, src/logger.py
  requirements.txt     dependency ของ service นี้ (ดูหัวข้อข้อควรระวัง)
  .env.example         ตัวแปรที่ service ต้องใช้
  run.sh               รัน consumer.py ด้วย python ใน .venv ของ service
  docker/              Dockerfile ของ service
scripts/               script ที่ Makefile เรียก: venv.sh, env.sh, gpu-drift.sh
dev_tools/             fake-gcs, patch ของ jax-unirep, ตัวส่งงานทดสอบ และตัววัดเวลาของ NCBI
```

entrypoint ของทุก service ต้องมี `sys.path.append("../../")` ก่อน import จาก `pkg` และทุก service มี venv ของตัวเองที่ `projects/<svc>/.venv` ขั้นตอนการเพิ่ม service ใหม่ซึ่งต้องแก้หลาย repo อยู่ที่ [how-to/add-ml-service.md](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/how-to/add-ml-service.md) ของ hub

## ข้อควรระวัง

- **requirements ถูกลงแบบถอด pin** version ที่ pin ไว้ใน `requirements.txt` ไม่มี wheel สำหรับ Python รุ่นใหม่ `make venv` จึงถอด pin ออกแล้วให้ pip เลือก version ล่าสุดที่เข้ากันได้ ยกเว้น `jax-unirep==2.2.0` ที่ต้องคงไว้ เพราะ 3.0.0 เปลี่ยน API จน evotune, fittop และ mutation ใช้ไม่ได้ ผลคือแต่ละเครื่องอาจได้ version ไม่ตรงกัน (BLB8)
- **jax-unirep ต้องใช้ patch และ `setuptools<81`** `jax-unirep` เรียก `jax.numpy.clip(x, a_min=-88)` ซึ่ง JAX รุ่นใหม่ไม่รับ และยัง `import pkg_resources` ซึ่งถูกถอดออกจาก setuptools ตั้งแต่ 81 `make venv` ลง `setuptools<81` และใส่ patch ให้เอง ถ้าสร้าง venv ด้วยมือ ให้รัน `make patch-jax` ต่อ รายละเอียดอยู่ใน [dev_tools/patches/README.md](./dev_tools/patches/README.md)
- **mmseqs2 ต้องตัด `bson` ออก** package `bson` เป็นของเก่าที่ build ไม่ผ่านบน Python ใหม่ และไม่จำเป็น เพราะ `pymongo` มี `bson` ของตัวเองอยู่แล้ว `make venv` ตัดให้เอง
- **ไฟล์ Swiss-Prot เก็บด้วย Git LFS** ถ้า `projects/mmseqs2/uniprot_sprot.fasta` มีขนาดแค่ไม่กี่ร้อย byte ให้รัน `git lfs pull`
- **service ack message ก่อนงานเสร็จ** ถ้า process ตายระหว่างรันงาน งานนั้นจะหาย และเพราะ queue เป็นแบบ exclusive message ที่ส่งมาตอนที่ service ไม่ได้ต่ออยู่จะหายไปเลย ปัญหาทั้งสองมีงานแก้อยู่ใน sub-issue ของ BLB5

## Deploy

ML service ของทั้ง dev และ production รันบน GPU VM นอก Kubernetes และไม่ได้อัปเดตจาก git หรือจาก image ของ repo นี้ การเอาโค้ดขึ้นเครื่องทำด้วยมือตาม [how-to/deploy-ml-service.md](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/how-to/deploy-ml-service.md) ของ hub (ต้องเป็นสมาชิกของ org จึงจะเปิดได้)

workflow `build-push consumer` ยัง build image ทุกครั้งที่ push ที่แตะ `projects/**` หรือ `pkg/common/**` บน `dev` และ `main` image นี้ไม่ได้ถูกใช้ เพราะ Deployment ใน cluster ถูกตรึงไว้ที่ 0 replica แต่ต้องเก็บไว้เผื่อต้องย้าย ML กลับเข้า cluster

## ลิงก์

- กติกาการทำงานและ hook ของ repo นี้: [CONTRIBUTING.md](./CONTRIBUTING.md)
- ข้อมูล service และเวลาที่ใช้: [reference/ml-services.md](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/reference/ml-services.md)
- การใช้ NCBI: [reference/ncbi.md](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/reference/ncbi.md)
