FROM python:3.11.6-slim

ARG SERVICE_NAME

WORKDIR /code

COPY . ./microservice

WORKDIR /code/microservice

RUN pip install --no-cache-dir --upgrade -r ./modules/common/requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./modules/${SERVICE_NAME}/requirements.txt

ENV SERVICE_NAME=${SERVICE_NAME}

CMD ["uvicorn", "cmd.microservice.${SERVICE_NAME}_microservice:app", "--host", "0.0.0.0", "--port", "8080"]