# fake-gcs (local only)

[fake-gcs-server](https://github.com/fsouza/fake-gcs-server) local ให้ ML pipeline รัน
end-to-end บน laptop ได้โดยไม่ต้องมี Google Cloud Storage credential จริง **dev กับ production
ไม่ใช้** — สองอันนั้นตั้ง credential จริงและปล่อย `STORAGE_EMULATOR_HOST` ว่างไว้

## Start / stop

```sh
docker compose -f dev_tools/fake-gcs/compose.yaml up -d
docker compose -f dev_tools/fake-gcs/compose.yaml down
```

แล้วตั้งค่านี้ในแต่ละ `projects/<svc>/.env` ที่จะรันกับมัน (และ **restart** consumer — `.env`
อ่านครั้งเดียวตอน startup):

```
STORAGE_EMULATOR_HOST=http://localhost:4443
```

`4443` เป็น default port ของ fake-gcs-server เอง `-p 4443:4443` แค่ publish ออกมา library
`google-cloud-storage` อ่าน `STORAGE_EMULATOR_HOST` เองแล้ว route request ทุกอันไปที่นั่นแทน
`storage.googleapis.com`

## Buckets

fake-gcs-server เปลี่ยนทุก top-level directory ใต้ `data/` เป็น bucket ตอน startup bucket ทั้ง 4
ของ pipeline เลยมีอยู่แล้ว:

| bucket | เขียนโดย | อ่านโดย |
| --- | --- | --- |
| `similar_protein` | `blast` / `mmseqs2` (query stage) | `evotune` |
| `unirep` | `evotune` | `fittop`, `mutation` |
| `ridgecv` | `fittop` | `mutation` |
| `mutation` | `mutation` (artifact สุดท้าย) | ปุ่ม download บน frontend |

เพิ่ม bucket: `mkdir dev_tools/fake-gcs/data/<name>` แล้ว restart container

## Inspect / reset

```sh
curl -s localhost:4443/storage/v1/b                       # list bucket
curl -s localhost:4443/storage/v1/b/similar_protein/o     # list object ใน bucket
```

object ที่เขียนถูกเก็บ **in memory** — `docker compose -f dev_tools/fake-gcs/compose.yaml down`
(หรือ `up` ใหม่) ล้างหมด ไม่มีอะไรเขียนกลับเข้า `data/` entry `data/*/*` ใน `.gitignore` เป็นแค่
safety net เผื่อ image version ในอนาคตเปลี่ยนพฤติกรรมนี้
