# Setup

This file is **local development**. The live dev + production deployment runs on the GPU
VM — see [docs/gpu-vm.md](./docs/gpu-vm.md).

## Run locally

Each of the 6 microservices under `projects/` (`blast`, `evotune`, `evotune_ESM`, `fittop`, `mmseqs2`, `mutation`) is set up the same way, but every one of them has its own venv and its own quirks - see the table below before you start.

1. **Env file** - each project already has `.env.local` pointing at a **local** broker (`RABBITMQ_URL=amqp://guest:guest@localhost:5672/`) with dummy/blank GCP creds. `consumer.py` loads plain `.env` (not `.env.local`), so copy it:

   ```sh
   cd projects/<project-name>
   cp .env.local .env
   ```

   So a locally-run consumer talks to a RabbitMQ **you** run (`docker run -p 5672:5672 -p 15672:15672 rabbitmq:3-management`), isolated - it never touches the dev or production queues. It gets no jobs until you publish one yourself (`dev_tools/rabbitmq/send_job.py`). GCP creds are blank, so GCS uploads fail at request time - fine for wiring/plumbing tests.

   **Never commit real GCP service-account credentials to any tracked file**

2. **Create a venv and install dependencies** - the pinned exact versions in each `requirements.txt` (`pandas==2.1.1`, `pydantic==2.5.2`, etc.) don't have prebuilt wheels for current Python and fail to build from source (needs a C/Rust compiler toolchain we don't have). Install **unpinned** instead and let pip resolve modern compatible versions:

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
   | `mmseqs2`                                      | drop `bson` from the install - it's a legacy/unmaintained package that fails to build on modern Python, and is unnecessary anyway: `pymongo` already provides `from bson import ObjectId` on its own |
   | `evotune`, `evotune_ESM`, `fittop`, `mutation` | also `pip install "setuptools<81"` - these use `jax-unirep`, which does `import pkg_resources` (part of setuptools); setuptools ≥81 dropped that module                                              |
   | `evotune_ESM`                                  | heaviest install (`torch`, `transformers`, `datasets`, `optuna`) - expect several minutes                                                                                                            |

3. **Run a microservice** - each project has a `run.sh` that copies `.env.local` → `.env` (first run only) and calls the venv's `python` directly, so you never have to remember to `source .venv/Scripts/activate` first. From the repo root:

   ```sh
   ./run.sh blast          # one service (or: cd projects/blast && ./run.sh)
   ./run.sh all            # every service, each backgrounded, Ctrl-C stops all
   ```

   (Runs `consumer.py`, the RabbitMQ-consumer entrypoint - currently the one actually used; `microservice.py` in each project is an older FastAPI entrypoint no longer wired up. If you'd rather run it manually: `source .venv/Scripts/activate` then `python consumer.py`.)

   Done when: logs show `Connecting to RabbitMQ` → `Connected to RabbitMQ` → `Consuming messages`, no crash. No HTTP port - it's a plain consumer, not a server. First run can take 20-30s before anything prints (slow `jax`/ML library import), that's normal, not a hang.

   Each microservice is its own blocking process with its own venv. `./run.sh all` backgrounds all of them (skipping `evotune_ESM` - it pulls `torch`; `RUN_ESM=1 ./run.sh all` to include it), but you usually only need the one(s) relevant to what you're testing, and every venv must already exist.

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
