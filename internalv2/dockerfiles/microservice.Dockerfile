FROM python:3.11.6-slim

ARG SERVICE_NAME

WORKDIR /code

COPY . ./microservice

WORKDIR /code/microservice

RUN pip install --no-cache-dir --upgrade -r ./libs/common.requirements.txt

RUN pip install --no-cache-dir --upgrade -r ./libs/${SERVICE_NAME}.requirements.txt

ENV SERVICE_NAME=${SERVICE_NAME}

CMD ["uvicorn", "cmd.${SERVICE_NAME}_microservice:app", "--host", "0.0.0.0", "--port", "8080"]