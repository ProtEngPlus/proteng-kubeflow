# dev_tools/patches

Local-only fixes applied **inside a project's `.venv`** (site-packages), for cases where a
pinned third-party package is incompatible with the interpreter/toolchain we actually run
locally. Site-package edits do not survive a reinstall, so **re-run the relevant script
after recreating a venv**. Never run these against the GPU VM.

## `fix_jax_unirep.py`

`jax-unirep` 2.2.0 (used by `evotune`, `fittop`, `mutation`, `evotune_ESM`) calls
`jax.numpy.clip(x, a_min=-88)` in `jax_unirep/activations.py`. Modern JAX removed the
`a_min` / `a_max` keyword arguments, so with the JAX version pip resolves locally
(`0.11.x`) those services crash:

```
TypeError: clip() got an unexpected keyword argument 'a_min'
```

The script rewrites that one call to the positional form `jax.numpy.clip(x, -88)`, which
means exactly the same thing (clip to a minimum of -88, no maximum) and is valid across
every JAX / NumPy version. It is idempotent and only touches the single known line.

```sh
python dev_tools/patches/fix_jax_unirep.py            # all four project venvs
python dev_tools/patches/fix_jax_unirep.py <path...>  # explicit activations.py paths
```

If a future JAX also drops `jax.example_libraries` (`evotuning_models.py`,
`optimizers.py` import from it), either extend this script or pin
`jax==0.4.25 jaxlib==0.4.25 "numpy<2"` in those four venvs.
