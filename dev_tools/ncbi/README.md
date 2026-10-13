# วัดเวลาของ NCBI BLAST

`ncbi_throughput_test.py` เรียก `NCBIWWW.qblast` ต่อกันหลายครั้งแล้วบันทึกเวลาที่แต่ละครั้งใช้ มีไว้เพื่อให้ได้ตัวเลขจริงว่า BLAST ผ่าน NCBI ใช้เวลาเท่าไร เพราะ query เดียวกันเคยใช้ตั้งแต่ประมาณ 1 นาทีไปจนถึงมากกว่า 45 นาที

script เรียก NCBI ด้วย parameter เดียวกับ blast service ใน `projects/blast/src/service/run_blast.py` คือ `blastp` กับ database `nr`, `expect=10.0`, `hitlist_size=50` และ socket timeout 180 วินาที และไม่ได้ import อะไรจาก pipeline เลย (ไม่มี RabbitMQ, consumer หรือ GCS) ตัวเลขที่ได้จึงเป็นเวลาของ NCBI ล้วน ๆ

## รัน

ตัวเลขจะตรงกับของจริงก็ต่อเมื่อรันบนเครื่องและเส้น network เดียวกับ blast service วิธีรันบนเครื่องที่ใช้ deploy อยู่ใน [reference/ncbi.md](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/reference/ncbi.md) ของ hub ถ้าแค่อยากลองในเครื่องตัวเอง ใช้ venv ของ blast

```sh
export NCBI_EMAIL="<อีเมลของคุณ>"
projects/blast/.venv/Scripts/python -u dev_tools/ncbi/ncbi_throughput_test.py --trials 3 --outfile ncbi_throughput.csv
```

บน Linux หรือ macOS ใช้ `projects/blast/.venv/bin/python` แทน

| option | default | ความหมาย |
| --- | --- | --- |
| `--trials` | `15` | จำนวนครั้งที่เรียก |
| `--outfile` | `ncbi_throughput.csv` | ไฟล์ผล เขียนต่อท้ายไฟล์เดิม |
| env `NCBI_EMAIL` | ไม่มี | อีเมลของผู้รัน NCBI ขอให้ส่งมากับทุก request ถ้าไม่ตั้ง script จะเตือน |

`run_throughput_batches.sh` รัน script นี้เป็นหลายรอบห่างกัน เพราะเวลาของ NCBI ขึ้นกับช่วงเวลาของวันมากกว่าจำนวนครั้ง ค่า default คือ 3 batch batch ละ 10 ครั้ง ห่างกัน 6 ชั่วโมง ต้องรันใน directory ที่มี `venv/` ของ blast และต้องตั้ง `NCBI_EMAIL` ก่อน

## ผล

ผลเป็น CSV หนึ่งแถวต่อหนึ่งครั้ง ในรูป `trial,start_utc,duration_s,status,hits,error` ถ้าเรียกไม่สำเร็จ `status` จะเป็น `fail` และ `error` บอกสาเหตุ

## ข้อควรระวัง

- ห้ามรันพร้อมกับ blast job ของ production เพราะหลาย request จาก IP เดียวกันเสี่ยงชน rate limit ของ NCBI
- `qblast` ของ Biopython หน่วงเวลาระหว่างการถามผลเองอยู่แล้ว (เริ่มที่ 20 วินาทีแล้วเพิ่มถึง 60 วินาทีสำหรับ host สาธารณะของ NCBI) การเรียกทีละครั้งจึงไม่ต้องหน่วงเพิ่ม
- script ตั้ง `NCBIWWW.email` และ `NCBIWWW.tool` ตามกติกาของ NCBI แต่ `run_blast.py` ของ blast service ยังไม่ได้ตั้ง งานแก้คือ BLB4
