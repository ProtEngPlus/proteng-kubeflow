# proteng-kubeflow

ML services of ProtEngPlus. Each service in `projects/<svc>/` is a RabbitMQ consumer for one pipeline stage (blast, mmseqs2, evotune, fittop, mutation; evotune_ESM is a proof of concept). The name is historical: nothing uses Kubeflow.

**This repo is public.** Never add IPs, SSH ports or users, host names, paths on the deploy machines, runbooks, or any credential, including in comments and commit messages. Those live in the private repos manual-guides-2023 and devops-infra; link to them instead.

## Commands

- `make check` before finishing any change: black `--check`, ruff and `bash -n`, same as CI. Needs `black==25.1.0` and `ruff==0.16.5`; bump them together with `.pre-commit-config.yaml` and the CI workflow.
- `make fmt` to apply black and ruff fixes.
- `make venv SVC=<svc>` to build or refresh one service venv; `make run SVC=<svc>` to run it (needs `make -C ../manual-guides-2023 infra-up`).
- `make send-job KEY=query.mmseqs2` publishes one query job to the local broker to test a single service.
- Run scripts with `bash <script>`: git stores them without the execute bit.

## Code layout

- `projects/<svc>/consumer.py` is the real entrypoint. `microservice.py` is the old FastAPI entrypoint and is not deployed.
- Shared code is in `pkg/common/` (RabbitMQ, GCS in `db.py`, logger). Entrypoints need `sys.path.append("../../")` before importing from `pkg`. A change in `pkg/common/` affects every service.
- Each service has its own venv at `projects/<svc>/.venv` and reads `projects/<svc>/.env` once at startup.
- `scripts/venv.sh`, `scripts/env.sh` and `scripts/gpu-drift.sh` hold the logic behind the Makefile.

## Things that break

- Production runs on Python 3.10. Do not use syntax or stdlib features newer than 3.10.
- Service venvs use Python 3.10 and install `requirements.txt` as pinned, with `projects/<svc>/constraints.txt` (the `pip freeze` of production) locking indirect dependencies. Do not "upgrade" jax-unirep (3.0.0 has a different API), aio_pika (10.x needs Python 3.11) or aiormq (7.x needs Python 3.11). After changing `requirements.txt`, regenerate `constraints.txt` from production as described in the hub.
- jax services need `setuptools<81` and the patch in `dev_tools/patches/fix_jax_unirep.py`. `make venv` does both.
- mmseqs2 must not install the `bson` package; `pymongo` provides `bson`.
- `STORAGE_EMULATOR_HOST` is for local runs only. Never set it in anything that runs real jobs.
- Queues are exclusive and messages are acked before the job finishes, so a consumer that disconnects or dies loses work silently. Keep this in mind before changing connection or ack handling; the fix is tracked under BLB5.
- `blast` calls NCBI through `NCBIWWW.qblast`, which has no overall timeout. Respect NCBI usage rules (`email`, `tool`, no parallel bursts).
- Merging into `dev` deploys the dev consumers on the GPU VM automatically a few minutes after CI passes, so a red CI blocks the deploy. Each consumer finishes its running job before it restarts, and a consumer that does not come back is rolled back. Production (`main`) is still copied by hand. Pushes touching `projects/**` or `pkg/common/**` build images that are not used (cluster replicas are 0).

## Team workflow

Issue first with a commit plan, branch from `dev`, Conventional Commits in English with one topic per commit, PR into `dev` using the template in Thai, no emoji anywhere. Full rules: `CONTRIBUTING.md` of manual-guides-2023.
