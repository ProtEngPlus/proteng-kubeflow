FROM python:3.11.6-slim

WORKDIR /code

COPY /example-microservice ./example-microservice

COPY /common ./common

RUN pip install --no-cache-dir --upgrade -r example-microservice/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]