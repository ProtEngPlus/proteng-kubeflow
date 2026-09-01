# dev_tools/patches

fix เฉพาะ local ที่ apply **ข้างใน `.venv` ของแต่ละ project** (site-packages) สำหรับกรณีที่
package third-party ที่ pin ไว้เข้ากันไม่ได้กับ interpreter/toolchain ที่เรารัน local จริง การแก้
site-package ไม่รอด reinstall เพราะงั้น **รัน script ใหม่หลังสร้าง venv ใหม่** อย่ารันกับ GPU VM

## `fix_jax_unirep.py`

`jax-unirep` 2.2.0 (ใช้โดย `evotune`, `fittop`, `mutation`, `evotune_ESM`) เรียก
`jax.numpy.clip(x, a_min=-88)` ใน `jax_unirep/activations.py` JAX ใหม่เอา keyword argument
`a_min` / `a_max` ออกแล้ว เพราะงั้นกับ JAX version ที่ pip resolve local (`0.11.x`) service พวกนี้
จะ crash:

```
TypeError: clip() got an unexpected keyword argument 'a_min'
```

script เขียน call นั้นใหม่เป็นแบบ positional `jax.numpy.clip(x, -88)` ซึ่งความหมายเดียวกันเป๊ะ
(clip ที่ค่าต่ำสุด -88 ไม่มีค่าสูงสุด) และใช้ได้กับทุก version ของ JAX / NumPy idempotent และแตะแค่
บรรทัดเดียวที่รู้

```sh
python dev_tools/patches/fix_jax_unirep.py            # venv ทั้ง 4 project
python dev_tools/patches/fix_jax_unirep.py <path...>  # ระบุ path ของ activations.py เอง
```

ถ้า JAX ในอนาคตเอา `jax.example_libraries` ออกด้วย (`evotuning_models.py`, `optimizers.py`
import จากมัน) ให้ต่อ script นี้ หรือ pin `jax==0.4.25 jaxlib==0.4.25 "numpy<2"` ใน venv ทั้ง 4
