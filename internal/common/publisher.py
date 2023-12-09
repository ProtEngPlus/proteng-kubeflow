import pika
from pydantic import BaseModel
from typing import Optional
import os

# TODO: Create a persistent connection to RabbitMQ instead


def publishDefaultExchange(rabbitmq_url, queue_name, message):
    # Create connection and channel
    connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
    channel = connection.channel()

    # Declare queue
    channel.queue_declare(queue=queue_name, durable=True)

    # Publish message
    channel.basic_publish(exchange="", routing_key=queue_name, body=message)

    # Close connection
    connection.close()


class Artifact(BaseModel):
    bucket_name: str
    path: str
    url: Optional[str] = ""


class JobUpdateData(BaseModel):
    job_id: str
    stage_id: int
    status: str
    artifact: Artifact
    error: Optional[str] = ""


class JobStatusEventMessage(BaseModel):
    service_name: str
    timestamp: str
    data: JobUpdateData


def publishJobStatusEvent(message: JobStatusEventMessage):
    rabbitmq_url = os.environ.get("RABBITMQ_URL")
    queue_name = "job_status_event"
    print(rabbitmq_url)
    try :
        publishDefaultExchange(rabbitmq_url, queue_name, message.json())
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")


if __name__ == "__main__":
    # TEST: publishJobStatusEvent

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
