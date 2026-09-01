# Contributing

กติกา commit message / branch / PR กับวิธีติดตั้ง pre-commit ของทุก repo ProtEngPlus เขียนรวมไว้ที่
[manual-guides-2023/CONTRIBUTING.md](https://github.com/ProtEngPlus/manual-guides-2023/blob/main/CONTRIBUTING.md)
repo นี้เก็บแค่ hook เฉพาะของตัวเอง

## Pre-commit hooks

- **pre-commit / pre-push**: `black` (format) + `ruff --fix` (lint) กับไฟล์ Python ที่ staged
- **commit-msg**: ปฏิเสธ commit message ที่ผิดฟอร์แมต Conventional Commits

`black --check` + `ruff check` (ไม่ autofix) รันใน CI (`.github/workflows/test-build-dev.yaml`) ทุก
push ด้วย CI ลง `black` / `ruff` เวอร์ชันเดียวกับ `.pre-commit-config.yaml` เป๊ะ — bump ตัวไหน bump
ทั้งคู่ ไม่งั้น local กับ CI เห็นไม่ตรงกัน `ruff.toml` ตั้ง `select` ชัดเจนไว้กันกฎเลื่อนตามเวอร์ชัน

`ruff` จับมากกว่าแค่เรื่อง format เช่น blind `except Exception:`, `datetime.now()` แบบไม่มี tz,
raise/except ที่ไม่จำเป็น พวกนี้ต้องใช้วิจารณญาณต่อจุด `ruff check --fix .` ไม่แตะให้ (ดู ignore list
ใน [ruff.toml](./ruff.toml))

รันมือทั้งหมด: `pre-commit run --all-files`
