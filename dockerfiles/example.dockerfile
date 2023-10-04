FROM python:3.11.6-slim

WORKDIR /app

COPY ./src/python .

ENTRYPOINT [ "python3", "cmd/blast.py" ]