# NCBI BLAST throughput test

`ncbi_throughput_test.py` เรียก `NCBIWWW.qblast` ต่อเนื่อง N ครั้ง แล้วบันทึกเวลาที่แต่ละครั้งใช้
จุดประสงค์: ได้ latency distribution จริงของ BLAST-ผ่าน-NCBI (query เดียวกันเคยเห็นตั้งแต่ ~1 นาที
ถึง 45+ นาที) แทนที่จะอ้างลอย ๆ

เรียกแบบเดียวกับ blast service (`projects/blast/src/service/run_blast.py`): `blastp` / `nr`,
`expect=10.0`, `hitlist_size=50`, socket timeout 180 วิ ไม่ได้ import อะไรจาก pipeline
(ไม่มี RabbitMQ / consumer / GCS) ตัวเลขที่ได้จึงเป็นเวลาของ NCBI ล้วน ๆ

## Run

ต้องรันบนเครื่อง + เส้น network เดียวกับ blast service เสมอ ผลถึงจะตรง production
VM ไม่มี checkout repo — copy `ncbi_throughput_test.py` เข้าไปที่ `~/proteng-gpu/apps/blast/` ก่อน
(อย่า paste ผ่าน terminal ไฟล์จะเพี้ยน — ใช้ `scp` หรือ `base64 -w0` / `base64 -d` แล้วเทียบ `md5sum`)

```sh
cd ~/proteng-gpu/apps/blast
export HTTP_PROXY=http://localhost:18888 HTTPS_PROXY=http://localhost:18888
export NCBI_EMAIL="you@example.com" # อีเมลจริง

# รันเดียว 15 ครั้ง
nohup venv/bin/python -u ncbi_throughput_test.py \
    --trials 15 --outfile ~/ncbi_throughput.csv > ~/ncbi_throughput.log 2>&1 &
```

`localhost:18888` = HTTP proxy ผ่าน SSH tunnel เส้นเดียวกับที่ consumer ใช้

#### ถ้าอยากกระจายหลายช่วงเวลา...

เวลา BLAST ขึ้นกับ time-of-day (peak US ช้ากว่า off-peak ชัด) การเก็บ 50 ครั้งรวดในหน้าต่างเดียว
ไม่ได้ดีกว่า 15 มากนัก — ควรกระจายช่วงเวลาแทน ใช้ `run_throughput_batches.sh` (copy เข้า VM คู่กับ
`ncbi_throughput_test.py`):

```sh
cd ~/proteng-gpu/apps/blast
export HTTP_PROXY=http://localhost:18888 HTTPS_PROXY=http://localhost:18888
export NCBI_EMAIL="you@example.com" # อีเมลจริง
chmod +x run_throughput_batches.sh
nohup ./run_throughput_batches.sh > ~/ncbi_throughput.log 2>&1 &
```

`run_throughput_batches.sh` default: 3 batch x 10 ครั้ง ห่างกัน 6 ชม.

## Output

```sh
cat ~/ncbi_throughput.csv
```

```sh
tail ~/ncbi_throughput.log
```

- ผลลัพธ์เป็น `ncbi_throughput.csv` — 1 แถวต่อ trial: `trial,start_utc,duration_s,status,hits,error`
- **ห้ามรันพร้อม BLAST job production จริง** — 2 request stream จาก IP เดียวเสี่ยงโดน NCBI rate limit
- ถ้า proxy tunnel หลุดระหว่างรัน batch นั้น fail (CSV บันทึก `status=fail`) — เช็ค `tail log` ด้วย

## หมายเหตุ

- `qblast` ของ Biopython throttle ตัวเองอยู่แล้ว (poll delay เริ่ม 20 วิ เพิ่มเป็น 60 วิ กับ host
  สาธารณะของ NCBI) เรียกแบบ sequential จึงไม่ต้องเพิ่ม throttle เอง
- Biopython 1.81 (ที่ติดตั้งบน VM) รองรับ `NCBIWWW.email` / `NCBIWWW.tool` แล้ว — script ตั้งให้
  พารามิเตอร์ทั้งสองถูกส่งไป NCBI จริงเมื่อยิง host สาธารณะ
- `run_blast.py` (production) **ยังไม่ได้ตั้ง** `NCBIWWW.email` / `NCBIWWW.tool` — เป็น NCBI-usage-policy
  fix ที่ควรทำ (bug B4)
