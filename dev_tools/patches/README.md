# patch ของ package ใน venv

โฟลเดอร์นี้เก็บ script ที่แก้ package ของบุคคลที่สามข้างใน `.venv` ของแต่ละ service สำหรับกรณีที่ version ที่ต้องใช้เข้ากับ library รุ่นใหม่ไม่ได้ การแก้ใน site-packages จะหายทุกครั้งที่ลง package ใหม่ จึงต้องรันซ้ำหลังสร้าง venv ใหม่ทุกครั้ง `make venv` รันให้เองแล้ว

## `fix_jax_unirep.py`

`jax-unirep` 2.2.0 ซึ่ง `evotune`, `fittop`, `mutation` และ `evotune_ESM` ใช้ เรียก `jax.numpy.clip(x, a_min=-88)` ใน `jax_unirep/activations.py` JAX รุ่นใหม่ไม่รับ keyword `a_min` และ `a_max` แล้ว service เหล่านี้จึง crash ด้วย error นี้

```text
TypeError: clip() got an unexpected keyword argument 'a_min'
```

script แก้บรรทัดนั้นเป็น `jax.numpy.clip(x, -88)` ซึ่งมีความหมายเหมือนเดิมทุกประการ (ตัดค่าที่ต่ำกว่า -88 และไม่มีค่าสูงสุด) และใช้ได้กับ JAX และ NumPy ทุกรุ่น script แตะแค่บรรทัดนี้บรรทัดเดียว และรันซ้ำได้ ถ้าแก้ไปแล้วจะบอกว่า `already patched`

```sh
make patch-jax                                        # ทุก venv ที่มีอยู่
python dev_tools/patches/fix_jax_unirep.py <path...>  # ระบุ activations.py เอง
```

ถ้า JAX รุ่นต่อไปเอา `jax.example_libraries` ออกด้วย ซึ่ง `evotuning_models.py` และ `optimizers.py` ของ `jax-unirep` ยัง import อยู่ ให้เพิ่มการแก้ใน script นี้ หรือ pin `jax==0.4.25`, `jaxlib==0.4.25` และ `numpy<2` ใน venv ของทั้ง 4 service

ห้ามรัน script นี้กับเครื่องที่รันงานจริงโดยไม่ได้ตั้งใจ venv บนเครื่องนั้นใช้ package คนละรุ่นกับในเครื่องของคุณ
