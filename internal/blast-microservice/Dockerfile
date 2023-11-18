FROM python:3.11.6-slim

WORKDIR /code

COPY /blast-microservice ./microservice

COPY /common ./common

RUN pip install --no-cache-dir --upgrade -r microservice/requirements.txt

WORKDIR /code/microservice

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]