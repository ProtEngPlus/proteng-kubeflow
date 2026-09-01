# proteng-kubeflow

repo นี้คือที่สร้าง _**docker image ของ microservice**_ สำหรับ ML pipeline

PS. ตอนแรกกลุ่ม proteng รุ่นแรกที่ทำ project นี้วางแผนจะใช้ kubeflow ทำ pipeline (ชื่อ repo เลย
เป็น "kubeflow") แต่ทีหลังตัดสินใจไม่ใช้ อ่านเพิ่มได้ที่
[devops repository](https://github.com/ProtEngPlus/manual-guides-2023/tree/main/devops)

วิธีรัน microservice บนเครื่อง local ดู [SETUP.md](./SETUP.md) กติกา commit กับ pre-commit hook ดู
[CONTRIBUTING.md](./CONTRIBUTING.md) และ **[docs/gpu-vm.md](./docs/gpu-vm.md)** สำหรับ deployment
จริง — ตอนนี้ `ml-pipeline` ทั้งหมด (dev **และ** production) รันนอก cluster บน GPU VM ไม่ได้ใช้
image ที่ repo นี้ build โฟลเดอร์ `dev_tools/` เก็บ helper แยก (`ncbi/` throughput test)

เพิ่งเริ่มกับ ProtEngPlus? เริ่มที่ [Guidebook](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/README.md) ก่อน

## Project Structure

เป็น mono-repo แต่ละ project ใน `projects/` แยกขาดจากกัน (แต่ละตัวคือ `microservice` หนึ่งตัวของ
ML pipeline) โฟลเดอร์ `pkg` เก็บ service/ไฟล์ที่ใช้ร่วมกันข้าม microservice

<pre>
.
├── pkg                                 # shared package ที่ทุก module ใช้ได้
│   ├── common
│   |   ├── rabbitmq.py
│   |   └── requirements.txt            # แต่ละ pkg module ประกาศ dependency ของตัวเอง
|   └── some-library
|       ├── some_module.py
│       └── requirements.txt
|
└── projects
    |
    └── example
        ├── docker                      # แต่ละ project มีได้หลาย <b>Dockerfile</b> สำหรับ app คนละแบบ
        |   └── microservice.Dockerfile
        |                               # ไฟล์ <b>entrypoint</b> — แต่ละ project มีได้หลาย entrypoint แต่ละอันคือ 1 app
        ├── microservice.py             # entrypoint แบบ FastAPI (เวอร์ชันแรก)
        ├── consumer.py                 # entrypoint แบบ RabbitMQ (เวอร์ชันสอง) <b>(ตัวที่ใช้จริงตอนนี้)</b>
        |
        ├── requirements.txt            # <b>dependency</b> ของ microservice 'example'
        └── src                         # src ของ microservice 'example'
            ├── service                 # โฟลเดอร์ source code หลัก (logic ทั้งหมดของ service)
            │   └── train.py
            ├── const.py                # constant ของ microservice 'example'
            ├── logger.py               # logger สำหรับ logging ใน microservice
            └── data
                └── example_data.txt
</pre>

## วิธีเพิ่ม microservice ใหม่

- เพิ่ม microservice ใหม่ในโฟลเดอร์ `projects` ตาม structure ข้างบน
- library/common service ที่ใช้หลาย microservice เพิ่มในโฟลเดอร์ `pkg`
- ในบริบทของแต่ละ project การ import module จาก `pkg` ต้องมี `sys.path.append('../../')` ใน
  ไฟล์ entrypoint

## วิธีเอา microservice ไปใช้ใน ML pipeline

> **สถานะตอนนี้ (2026-09):** consumer ของ `ml-pipeline` รันบน GPU VM `isel-5090` ประกอบมือ
> **ไม่ได้**มาจาก image ข้างล่าง — ดู [docs/gpu-vm.md](./docs/gpu-vm.md) in-cluster consumer
> Deployment ถูกตรึง `replicas: 0` flow build image ข้างล่างยังใช้กับ image `evotune_ESM` /
> `*-rest` และถ้าย้ายกลับเข้า cluster ในอนาคต

จุดประสงค์ของ repo นี้คือพัฒนา microservice แล้ว build เป็น `docker image` ให้ ML pipeline ใช้
(วิธีเอา image เข้า ML pipeline อยู่ใน
[devops repository](https://github.com/ProtEngPlus/manual-guides-2023/tree/main/devops))

- context ของ Dockerfile แต่ละตัวอยู่ที่ root ของ project เพื่อให้ build โค้ดในโฟลเดอร์ `pkg` ได้ด้วย

### build docker image

```sh
docker build -t blast-service -f ./projects/blast/docker/microservice.Dockerfile .
```

### build + publish ขึ้น docker repository

- ไปที่ `Actions` ใน github
- เลือก `Build and Publish ML pipeline microservices`
- `run workflow` แล้วเลือก `microservice` ที่จะ build
  - ติ๊ก `auto deploy to devops-k8s` เพื่อ deploy ML pipeline อัตโนมัติหลัง build เสร็จ

### run docker local เพื่อทดสอบ image

- เปลี่ยน port ให้ตรงกับที่ระบุใน dockerfile

```sh
docker run -d --name blast-service -p 8080:8080 --env-file=".env" blast-service
```
