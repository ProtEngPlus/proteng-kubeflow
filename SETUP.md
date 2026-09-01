# Setup

This file is **local development**. The live dev + production deployment runs on the GPU
VM — see [docs/gpu-vm.md](./docs/gpu-vm.md).

## The 6 services

All 6 are the same shape: a RabbitMQ consumer (`consumer.py`) that binds an **exclusive**
queue on the `logs_topic` topic exchange with one routing key, runs one job on a background
thread, and publishes the result to the durable `job_status_event` queue (what
`proteng-conductor` reads back). They differ only in what the job does and what it needs at
run time.

| service | queue | routing key | pipeline stage | needs at run time | runs locally? |
| --- | --- | --- | --- | --- | --- |
| `blast` | `blast_queue` | `query.blast` | query | internet → NCBI BLAST (`NCBIWWW.qblast`) | yes |
| `mmseqs2` | `mmseqs2_queue` | `query.mmseqs2` | query | `mmseqs` binary on `PATH` + `projects/mmseqs2/uniprot_sprot.fasta` (committed) | yes, after the binary step below |
| `evotune` | `evotune_queue` | `evotune.unirep` | improvement | reads the query stage's artifact from GCS; `jax-unirep` (mlstm64 weights ship with the pip package) | yes, with the fake-gcs + `jax-unirep` patch below |
| `fittop` | `fittop_queue` | `fittop.ridgecv` | improvement | reads the `evotune` artifact from GCS; `jax-unirep` `get_reps` | yes, same |
| `mutation` | `mutation_queue` | `mutation.mutation` | improvement | reads the `evotune` + `fittop` artifacts from GCS; `jax-unirep` `get_reps` | yes, same |
| `evotune_ESM` | `evotune_ESM_queue` | `evotune.ESM` | improvement (POC, not wired into conductor) | GCS + Hugging Face model download (`AutoModelForMaskedLM.from_pretrained`) + `torch` (GPU ideally) | not covered |

Every stage's input is the previous stage's GCS output - no externally-supplied trained
models. With **blank GCP creds** you can run `blast` (up to the upload) and `mmseqs2` (same,
after installing the binary); a job dies with `PRIVATE_KEY is not set` at the first storage
call. Add the **local fake-gcs-server** (step 2) and the whole chain runs - see "Full
pipeline locally" below. `dev_tools/rabbitmq/send_job.py` publishes a single query-stage
job for isolated testing (pass the routing key, e.g. `query.mmseqs2`); the improvement
stages only get messages from the conductor.

## Run locally

Each of the 6 microservices under `projects/` (`blast`, `evotune`, `evotune_ESM`, `fittop`, `mmseqs2`, `mutation`) is set up the same way, but every one of them has its own venv and its own quirks - see the table below before you start.

1. **Env file** - each project already has `.env.local` pointing at a **local** broker (`RABBITMQ_URL=amqp://guest:guest@localhost:5672/`) with dummy/blank GCP creds. `consumer.py` loads plain `.env` (not `.env.local`), so copy it:

   ```sh
   cd projects/<project-name>
   cp .env.local .env
   ```

   So a locally-run consumer talks to a RabbitMQ **you** run (`docker run -p 5672:5672 -p 15672:15672 rabbitmq:3-management`), isolated - it never touches the dev or production queues. It gets no jobs until you publish one yourself (`dev_tools/rabbitmq/send_job.py`).

   **Never commit real GCP service-account credentials to any tracked file**

2. **GCS - blank creds, or a local emulator.** Every service reads/writes job
   artifacts through `pkg/common/db.py`. Two ways to run locally:

   - **Leave the GCP block blank** (default). The job runs and then raises
     `PRIVATE_KEY is not set` at the first GCS call - fine for testing the
     RabbitMQ wiring and everything up to storage.
   - **Point at a local [fake-gcs-server](https://github.com/fsouza/fake-gcs-server)**
     to let the job finish. A compose file with the four pipeline buckets
     pre-created lives at `dev_tools/fake-gcs/`:

     ```sh
     docker compose -f dev_tools/fake-gcs/compose.yaml up -d
     # then in each projects/<svc>/.env you want to run against it:
     STORAGE_EMULATOR_HOST=http://localhost:4443
     ```

     Consumers read `.env` **once at startup** - restart any that were already
     running. `4443` is fake-gcs-server's own default port; the
     `google-cloud-storage` library reads `STORAGE_EMULATOR_HOST` itself and
     routes every request there instead of `storage.googleapis.com`, so
     `getStorageClient()` only has to skip the service-account credentials. See
     `dev_tools/fake-gcs/README.md` for inspecting and resetting the store, and
     "Full pipeline locally" below for the end-to-end run.

   `STORAGE_EMULATOR_HOST` is **opt-in and local only** - it is committed blank in
   every `.env.example`, and the dev and production consumers on the GPU VM must
   never set it, or the library would silently route real jobs to a non-existent
   local emulator instead of GCS.

3. **Create a venv and install dependencies** - the pinned exact versions in each `requirements.txt` (`pandas==2.1.1`, `pydantic==2.5.2`, etc.) don't have prebuilt wheels for current Python and fail to build from source (needs a C/Rust compiler toolchain we don't have). Install **unpinned** instead and let pip resolve modern compatible versions:

   ```sh
   python -m venv .venv
   source .venv/Scripts/activate   # Windows Git Bash; macOS/Linux: source .venv/bin/activate
   sed 's/[=<>].*$//' requirements.txt > /tmp/req.txt   # strip version pins
   pip install -r /tmp/req.txt -r ../../pkg/common/requirements.txt
   ```

   Some `requirements.txt` files are saved as UTF-16 (not plain ASCII) - if `sed`/`grep` on one errors out or produces garbage, check with `file requirements.txt` first and decode via `iconv -f UTF-16LE -t UTF-8` before piping to `sed`.

   **Per-project extras** (on top of the above):

   | Project                                        | Extra step needed                                                                                                                                                                                    |
   | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | `blast`                                        | none                                                                                                                                                                                                 |
   | `mmseqs2`                                      | (1) drop `bson` from the install - it's a legacy/unmaintained package that fails to build on modern Python, and is unnecessary anyway: `pymongo` already provides `from bson import ObjectId` on its own. (2) needs the `mmseqs` binary on `PATH` - see below                                            |
   | `evotune`, `evotune_ESM`, `fittop`, `mutation` | also `pip install "setuptools<81"` - these use `jax-unirep`, which does `import pkg_resources` (part of setuptools); setuptools ≥81 dropped that module                                              |
   | `evotune_ESM`                                  | heaviest install (`torch`, `transformers`, `datasets`, `optuna`) - expect several minutes                                                                                                            |

   **`mmseqs2` - the `mmseqs` binary.** `run_mmseqs2.py` shells out to `mmseqs
   easy-search`, so the binary must be on `PATH` (there is no path override in
   the code). The search database (`projects/mmseqs2/uniprot_sprot.fasta`, ~286
   MB Swiss-Prot) is committed in the repo, so that part is already in place.

   - **Windows**: download
     <https://github.com/soedinglab/MMseqs2/releases/latest/download/mmseqs-win64.zip>
     (the `mmseqs.com/latest/` mirror only carries the Linux/macOS builds) and
     extract it, e.g. to `C:\Users\<you>\mmseqs`. The archive ships only
     `bin\mmseqs.exe` + `bin\busybox.exe`; `mmseqs easy-search` is a shell
     workflow that needs GNU-style tools, so install the BusyBox applets once:

     ```powershell
     C:\Users\<you>\mmseqs\bin\busybox.exe --install C:\Users\<you>\mmseqs\bin
     ```

     Then add **`...\mmseqs\bin`** (not the folder with `mmseqs.bat`) to your
     user `PATH` - `run_mmseqs2.py` calls `subprocess.run(["mmseqs", ...])`
     without a shell, and Windows process creation resolves `mmseqs.exe` but not
     `mmseqs.bat`:

     ```powershell
     [Environment]::SetEnvironmentVariable("Path",
       [Environment]::GetEnvironmentVariable("Path","User") + ";C:\Users\<you>\mmseqs\bin", "User")
     ```

   - **macOS**: `brew install mmseqs2`, or the `mmseqs-osx-universal.tar.gz` from
     the releases page. **Linux**: the static `mmseqs-linux-*.tar.gz` (pick
     `avx2` on a modern CPU, `sse41`/`sse2` otherwise) - put `mmseqs` on `PATH`.
   - Verify in a **new** terminal (close the `./run.sh` window too - it keeps the
     old `PATH`): `mmseqs version` prints a commit hash.

   Without it, `mmseqs2` jobs fail immediately with
   `FileNotFoundError: ... 'mmseqs'`. If you don't need to exercise `mmseqs2`
   locally, just skip this service - it runs fine on the GPU VM.

4. **Run a microservice** - each project has a `run.sh` that copies `.env.local` → `.env` (first run only) and calls the venv's `python` directly, so you never have to remember to `source .venv/Scripts/activate` first. From the repo root:

   ```sh
   ./run.sh blast          # one service (or: cd projects/blast && ./run.sh)
   ./run.sh all            # every service, each backgrounded, Ctrl-C stops all
   ```

   (Runs `consumer.py`, the RabbitMQ-consumer entrypoint - currently the one actually used; `microservice.py` in each project is an older FastAPI entrypoint no longer wired up. If you'd rather run it manually: `source .venv/Scripts/activate` then `python consumer.py`.)

   Done when: logs show `Connecting to RabbitMQ` → `Connected to RabbitMQ` → `Consuming messages`, no crash. No HTTP port - it's a plain consumer, not a server. First run can take 20-30s before anything prints (slow `jax`/ML library import), that's normal, not a hang.

   Each microservice is its own blocking process with its own venv. `./run.sh all` backgrounds all of them (skipping `evotune_ESM` - it pulls `torch`; `RUN_ESM=1 ./run.sh all` to include it), but you usually only need the one(s) relevant to what you're testing, and every venv must already exist.

## Full pipeline locally

Runs `blast|mmseqs2 → evotune → fittop → mutation` to **Completed** on one machine, driven
by the real `proteng-conductor`. Each stage hands the next one an artifact through a GCS
bucket, so every stage's input is the previous stage's output:

```
query (blast|mmseqs2) --> similar_protein --> evotune --> unirep --> fittop --> ridgecv --> mutation --> mutation
```

`evotune_ESM` is not part of this - it is a POC with no conductor stage.

1. **Infra**: RabbitMQ + Mongo (see step 1) + the GCS emulator:

   ```sh
   docker compose -f dev_tools/fake-gcs/compose.yaml up -d
   curl -s localhost:4443/storage/v1/b        # lists similar_protein, unirep, ridgecv, mutation
   ```

2. **Patch `jax-unirep`** for `evotune` / `fittop` / `mutation` (modern JAX removed the
   `jax.numpy.clip(a_min=...)` kwarg these still use):

   ```sh
   python dev_tools/patches/fix_jax_unirep.py
   ```

   Re-run this whenever you rebuild one of those venvs (see `dev_tools/patches/README.md`).

3. **App services** - from each repo, with its `.env.local` (defaults are already local -
   see each repo's `SETUP.md`):

   ```sh
   # proteng-user-mgmt, proteng-conductor, proteng-bff  (Git Bash, one terminal each)
   ./run.sh
   # protengplus-frontend
   npm run dev
   ```

4. **Consumers** - set `STORAGE_EMULATOR_HOST=http://localhost:4443` in each
   `projects/<svc>/.env` (`blast`, `mmseqs2`, `evotune`, `fittop`, `mutation`), then:

   ```sh
   ./run.sh all        # from the mmseqs-on-PATH shell; evotune_ESM is skipped
   ```

   All five reach `Consuming messages`.

5. **Submit** - in the frontend: sign up, create an **auto** job, choose a query tool,
   submit. Watch the consumer logs go
   `mmseqs2 … completed` → `evotune … completed` → `fittop … completed` →
   `mutation … completed`; the UI job flips to **Completed**. Confirm the final artifact:

   ```sh
   curl -s localhost:4443/storage/v1/b/mutation/o
   ```

The job-config values the frontend sends can look odd (e.g. `e: 70`, `min_seq_id: 70`) -
that is a known frontend typing bug (the `e` field is typed `percent` in
`createJobConfig.ts`), not something wrong with your setup, and it does not block the run.

## Format

`black` autofixes on commit/push. Run manually against the whole repo:

```sh
black .
```

## Lint

`ruff` autofixes most issues on commit/push. Run manually:

```sh
ruff check --fix .
```

`black --check` and `ruff check` (no autofix) also run in CI (`.github/workflows/test-build-dev.yaml`) on every push. CI installs `black` / `ruff` **pinned to the same versions as `.pre-commit-config.yaml`** - when you bump one, bump both, or local and CI disagree about what passes. `ruff.toml` sets an explicit `select` so the rule set does not shift with the ruff version.

## Pre-commit hooks

Format + lint above run automatically via [pre-commit](https://pre-commit.com/) on both `git commit` and `git push`. See [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

Install once per clone:

```sh
pip install pre-commit
pre-commit install --hook-type pre-commit --hook-type pre-push --hook-type commit-msg
```

Run everything manually: `pre-commit run --all-files`

The `git commit` / `git push` hooks call `pre-commit` by its full path, so they
work even when `pre-commit` is not on your `PATH`. Running it manually may not:
`pip install --user` (and conda-base pip on Windows) puts the executable somewhere
off `PATH`. If `pre-commit` is "not recognized", invoke it directly, e.g.
`python -m pre_commit run --all-files`, or add its `Scripts` dir to `PATH`.
