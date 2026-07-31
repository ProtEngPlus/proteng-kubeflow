#!/usr/bin/env bash
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.local .env
fi

if [ -f .venv/Scripts/python.exe ]; then
  PYTHON=.venv/Scripts/python.exe
elif [ -f .venv/bin/python ]; then
  PYTHON=.venv/bin/python
else
  echo "No .venv found — see SETUP.md to create one first."
  exit 1
fi

"$PYTHON" consumer.py
