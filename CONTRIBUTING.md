# Contributing

กติกาเรื่อง branch, commit message, PR และ docs ของทุก repo อยู่ที่ [CONTRIBUTING.md ของ hub](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/CONTRIBUTING.md) หน้านี้มีเฉพาะเรื่องของ proteng-kubeflow

- แตก branch จาก `dev` และเปิด PR เข้า `dev`
- รัน `make check` ก่อน push ทุกครั้ง คำสั่งนี้ตรวจแบบเดียวกับ CI คือ `black --check`, `ruff check` และ `bash -n` กับ script
- repo นี้เป็น public ห้ามใส่ credential และรายละเอียดของเครื่องที่ใช้ deploy
- การ merge ไม่ได้ทำให้โค้ดขึ้น GPU VM ต้องเอาขึ้นเองตาม [how-to/deploy-ml-service.md](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/how-to/deploy-ml-service.md) ของ hub

## แก้คู่กับ repo อื่น

ของต่อไปนี้ต้องแก้พร้อมกับอีก repo ในงานชุดเดียวกัน และ PR ของทั้งสองฝั่งต้องใส่ `Related: ProtEngPlus/<repo>#<เลข PR>` ถึงกัน รายการเต็มและลำดับการ merge อยู่ใน [CONTRIBUTING ของ hub](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/CONTRIBUTING.md#ของที่ต้องแก้คู่กันข้าม-repo)

- routing key ใน `consumer.py` ต้องตรงกับชื่อ tool ใน `createJobConfig.ts` ของ frontend และชื่อ stage ใน conductor
- การอ่าน message และการส่งผลใน `pkg/common` ต้องตรงกับ struct ใน `internal/conductor/model.go` ของ conductor
- ถ้าเพิ่ม service หรือ queue ใหม่ ต้องเพิ่มใน `SERVICES` ของ `Makefile` และ `EXPECTED_QUEUES` ใน `ops/lib.sh` ของ devops-infra

## hook

`make setup` ติดตั้ง hook ให้ด้วย pre-commit

| ตอน | hook |
| --- | --- |
| commit และ push | `black` จัด format และ `ruff --fix` แก้ปัญหาที่แก้เองได้ กับไฟล์ Python ที่ staged |
| เขียน commit message | ปฏิเสธ message ที่ไม่ตรงกับ Conventional Commits |

- CI ใช้ `black==25.1.0` และ `ruff==0.16.5` ซึ่งตรงกับ `.pre-commit-config.yaml` ถ้าจะเปลี่ยน version ต้องเปลี่ยนทั้งสองที่พร้อมกัน ไม่อย่างนั้นผลในเครื่องกับใน CI จะไม่ตรงกัน
- `ruff.toml` ระบุกฎที่ใช้ไว้ชัดเจนใน `select` กฎจึงไม่เปลี่ยนเองเมื่ออัปเดต ruff
- ruff จับเรื่องที่มากกว่า format เช่น `except Exception:` แบบกว้าง, `datetime.now()` ที่ไม่มี timezone และ raise หรือ except ที่ไม่จำเป็น เรื่องเหล่านี้ `ruff check --fix` ไม่แก้ให้ ต้องตัดสินใจเองทีละจุด ดูรายการที่ ignore ไว้ใน [ruff.toml](./ruff.toml)
- ถ้า hook แก้ไฟล์ให้ระหว่าง commit ให้ `git add` ไฟล์นั้นซ้ำแล้ว commit อีกครั้ง
