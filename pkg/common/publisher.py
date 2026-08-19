import datetime
import logging
import os
from typing import Any

import pika
from pydantic import BaseModel

# TODO: Create a persistent connection to RabbitMQ instead

logger = logging.getLogger("rabbitmq_publisher")


def publishDefaultExchange(rabbitmq_url, queue_name, message):
    connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name, durable=True)

    channel.basic_publish(exchange="", routing_key=queue_name, body=message)

    connection.close()


class Artifact(BaseModel):
    bucket_name: str
    path: str
    url: str | None = ""


class JobUpdateData(BaseModel):
    job_id: str
    stage_id: int
    status: str
    artifact: Artifact
    error: str | None = ""
    mutation_id: str | None = ""
    mutation_result: dict[str, float] | None = {}
    query_result_id: str | None = ""
    query_result: list[dict[str, Any]] | None = []


class JobStatusEventMessage(BaseModel):
    service_name: str
    timestamp: str
    data: JobUpdateData


def publishJobStatusEvent(message: JobStatusEventMessage):
    rabbitmq_url = os.environ.get("RABBITMQ_URL")
    queue_name = "job_status_event"

    try:
        publishDefaultExchange(rabbitmq_url, queue_name, message.json())
    except Exception as err:  # noqa: BLE001 -- failure is logged, not fatal
        logger.warning(f"error publishing Message: Unexpected {err=}, {type(err)=}")


if __name__ == "__main__":
    # TEST: publishJobStatusEvent
    os.environ.update([("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")])
    print(datetime.datetime.now(datetime.timezone.utc).isoformat())
    message = JobStatusEventMessage(
        service_name="job",
        timestamp="2021-01-01T00:00:00.000Z",
        data=JobUpdateData(
            job_id="job_id",
            stage_id=1,
            status="completed",
            artifact=Artifact(bucket_name="bucket_name", path="path", url="url"),
            error="error",
        ),
    )
    publishJobStatusEvent(message)
