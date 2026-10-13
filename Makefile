# proteng-kubeflow: the ML pipeline consumers (blast, mmseqs2, evotune, fittop,
# mutation, evotune_ESM). Run `make` to list targets. Works from Git Bash, cmd or PowerShell (needs Git for Windows).

# On Windows, `bash` found from cmd or PowerShell is often the WSL launcher
# (C:\Windows\System32\bash.exe), so use the bash that ships with Git for Windows.
# Git's layout is <root>/mingw64/libexec/git-core and <root>/bin/bash.exe.
ifeq ($(OS),Windows_NT)
GIT_EXEC_PATH := $(shell git --exec-path)
ifneq ($(findstring /mingw64/libexec/git-core,$(GIT_EXEC_PATH)),)
SHELL := $(subst /mingw64/libexec/git-core,/bin/bash.exe,$(GIT_EXEC_PATH))
else
SHELL := bash
endif
else
SHELL := bash
endif
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory

SERVICES := blast mmseqs2 evotune fittop mutation
SVC ?=
KEY ?= query.mmseqs2
ENV ?= all
REF ?= HEAD
GPU_VM ?= proteng-gpu
# python3 on Windows is often the Microsoft Store stub, so check that it runs.
PYTHON ?= $(shell python3 -c 'import sys' >/dev/null 2>&1 && echo python3 || echo python)
# Python inside one service venv (Windows or Linux layout).
venv_python = $(firstword $(wildcard projects/$(1)/.venv/Scripts/python.exe projects/$(1)/.venv/bin/python))

.PHONY: help setup hooks env env-local-gcs venv venvs patch-jax run run-all gcs-up gcs-down \
	send-job lint fmt check docker-build gpu-status gpu-drift

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*## "} /^##@/ {printf "\n%s\n", substr($$0, 5)} /^[a-zA-Z0-9_.-]+:.*## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

##@ Setup
setup: hooks env venvs ## First-time setup: git hooks, .env files and the 5 service venvs

hooks: ## Install the git hooks (needs `pip install pre-commit`)
	$(PYTHON) -m pre_commit install --hook-type pre-commit --hook-type pre-push --hook-type commit-msg

env: ## Create projects/*/.env from .env.example (never overwrites)
	bash scripts/env.sh

env-local-gcs: ## Also point every .env at the local fake-gcs emulator (local only)
	bash scripts/env.sh --local-gcs

venv: ## Create or update one service venv (SVC=blast|mmseqs2|evotune|fittop|mutation|evotune_ESM)
	@if [ -z "$(SVC)" ]; then echo "usage: make venv SVC=<service>"; exit 2; fi
	PYTHON=$(PYTHON) bash scripts/venv.sh $(SVC)

venvs: ## Create or update the venvs of the 5 pipeline services (ESM=1 adds evotune_ESM)
	@for s in $(SERVICES) $(if $(ESM),evotune_ESM); do PYTHON=$(PYTHON) bash scripts/venv.sh $$s; done

patch-jax: ## Re-apply the jax-unirep clip patch to every existing venv
	$(PYTHON) dev_tools/patches/fix_jax_unirep.py

##@ Run locally (needs RabbitMQ; `make -C ../manual-guides-2023 infra-up`)
run: ## Run one consumer in the foreground (SVC=...)
	@if [ -z "$(SVC)" ]; then echo "usage: make run SVC=<service>"; exit 2; fi
	bash run.sh $(SVC)

run-all: ## Run every consumer in the background, Ctrl-C stops all (RUN_ESM=1 adds evotune_ESM)
	bash run.sh all

gcs-up: ## Start the local fake-gcs emulator on localhost:4443
	docker compose -f dev_tools/fake-gcs/compose.yaml up -d

gcs-down: ## Stop fake-gcs (this also deletes every object it stored)
	docker compose -f dev_tools/fake-gcs/compose.yaml down

send-job: ## Publish one query job to the local broker (KEY=query.mmseqs2|query.blast)
	@py="$(call venv_python,$(or $(SVC),mmseqs2))"; \
	  if [ -z "$$py" ]; then echo "no venv yet: run make venv SVC=$(or $(SVC),mmseqs2)"; exit 2; fi; \
	  "$$py" dev_tools/rabbitmq/send_job.py $(KEY)

##@ Checks
lint: ## black --check, ruff check and bash -n (same as CI)
	$(PYTHON) -m black --check .
	$(PYTHON) -m ruff check .
	@for f in run.sh scripts/*.sh projects/*/run.sh; do bash -n "$$f"; done

fmt: ## Format with black and apply ruff fixes
	$(PYTHON) -m black .
	$(PYTHON) -m ruff check --fix .

check: lint ## Everything CI checks (needs `pip install black==25.1.0 ruff==0.16.5`)

docker-build: ## Build one consumer image locally (SVC=...)
	@if [ -z "$(SVC)" ]; then echo "usage: make docker-build SVC=<service>"; exit 2; fi
	docker build -t proteng-$(SVC) -f projects/$(SVC)/docker/consumer.Dockerfile .

##@ GPU VM (ssh alias proteng-gpu, see how-to/access.md in manual-guides-2023)
gpu-status: ## Tunnels and consumers on the GPU VM
	ssh $(GPU_VM) '~/proteng-gpu/bin/status-all.sh'

gpu-drift: ## Compare code in git with the GPU VM, report only (ENV=dev|prod|all, REF=HEAD)
	GPU_SSH="ssh $(GPU_VM)" bash scripts/gpu-drift.sh $(ENV) $(REF)
