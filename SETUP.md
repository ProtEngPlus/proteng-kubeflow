# Setup

## Run locally

1. **Create a `.env` file** inside the microservice's project folder (e.g. `projects/blast/.env`) — **never commit real GCP service-account credentials to any tracked file** (a previous copy of this README leaked a live key — flag to a maintainer if not already rotated):
   ```
   PROJECT_ID=
   PRIVATE_KEY_ID=
   PRIVATE_KEY=
   CLIENT_EMAIL=
   CLIENT_ID=
   TOKEN_URI=https://oauth2.googleapis.com/token
   RABBITMQ_URL=amqp://<user>:<pass>@rabbitmq:5672/
   ```
   Get real values from a maintainer via a secret manager or private channel — not Notion/README/git. Done when: `.env` exists with real values.

2. **Run RabbitMQ locally**
   ```sh
   docker run --name rabbitmq-for-test -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management
   ```
   Done when: `docker ps` shows the container healthy/running.

3. **Run a microservice**
   ```sh
   cd projects/<project-name>
   python3 <entrypoint>.py
   ```
   e.g. `cd projects/blast && python3 microservice.py`. Done when: process starts and connects to RabbitMQ without erroring.

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

## Pre-commit hooks

Format + lint above run automatically via [pre-commit](https://pre-commit.com/) on both `git commit` and `git push`. See [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

Install once per clone:

```sh
pip install pre-commit
pre-commit install --hook-type pre-commit --hook-type pre-push --hook-type commit-msg
```

Run everything manually: `pre-commit run --all-files`
