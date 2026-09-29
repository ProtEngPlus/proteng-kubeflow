#!/usr/bin/env bash
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
fi

if [ -f .venv/Scripts/python.exe ]; then
  PYTHON=.venv/Scripts/python.exe
elif [ -f .venv/bin/python ]; then
  PYTHON=.venv/bin/python
else
  echo "No .venv found - run: make venv SVC=fittop (from the repo root)"
  exit 1
fi

"$PYTHON" consumer.py
