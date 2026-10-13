# fake-gcs (ใช้ในเครื่องเท่านั้น)

[fake-gcs-server](https://github.com/fsouza/fake-gcs-server) จำลอง Google Cloud Storage ในเครื่อง ML service จึงรัน pipeline ได้จนจบโดยไม่ต้องมี credential ของ GCP dev และ production ไม่ได้ใช้ตัวนี้ และต้องไม่ตั้ง `STORAGE_EMULATOR_HOST`

## เปิดและปิด

ปกติ fake-gcs ถูกเปิดพร้อม RabbitMQ และ MongoDB ด้วย `make infra-up` ของ manual-guides-2023 ถ้าจะเปิดแยก ให้ใช้ `make gcs-up` และ `make gcs-down` ที่ root ของ repo นี้

จากนั้นชี้ service ทุกตัวไปที่ emulator ด้วย `make env-local-gcs` ซึ่งตั้งค่านี้ใน `projects/<svc>/.env` แล้ว restart service ที่รันอยู่ เพราะ `.env` ถูกอ่านแค่ตอนเริ่ม

```text
STORAGE_EMULATOR_HOST=http://localhost:4443
```

`4443` เป็น port default ของ fake-gcs-server library `google-cloud-storage` อ่าน `STORAGE_EMULATOR_HOST` เองแล้วส่ง request ทั้งหมดไปที่นั่นแทน `storage.googleapis.com`

## bucket

ตอนเริ่ม fake-gcs-server จะเปลี่ยนทุก directory ชั้นแรกใต้ `data/` ให้เป็น bucket bucket ทั้ง 4 ที่ pipeline ใช้จึงมีอยู่แล้วโดยไม่ต้องสร้างเอง

| bucket | เขียนโดย | อ่านโดย |
| --- | --- | --- |
| `similar_protein` | `blast` หรือ `mmseqs2` (stage query) | `evotune` |
| `unirep` | `evotune` | `fittop` และ `mutation` |
| `ridgecv` | `fittop` | `mutation` |
| `mutation` | `mutation` (artifact สุดท้าย) | ปุ่ม download บนหน้าเว็บ |

ถ้าต้องการ bucket เพิ่ม ให้สร้าง directory ด้วย `mkdir dev_tools/fake-gcs/data/<ชื่อ>` แล้ว restart container

## ดูและล้างข้อมูล

```sh
curl -s localhost:4443/storage/v1/b                       # รายชื่อ bucket
curl -s localhost:4443/storage/v1/b/similar_protein/o     # object ใน bucket หนึ่ง
```

object ที่ service เขียนถูกเก็บไว้ใน memory เท่านั้น การปิดด้วย `make gcs-down` หรือ `make infra-down` จะล้างทั้งหมด และไม่มีอะไรถูกเขียนกลับลง `data/` บรรทัด `data/*/*` ใน `.gitignore` มีไว้กันเผื่อ image รุ่นต่อไปเปลี่ยนพฤติกรรมนี้
