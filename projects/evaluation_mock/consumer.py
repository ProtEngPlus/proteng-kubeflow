import asyncio
import json
import os
import sys
import threading

sys.path.append("../../")

import aio_pika
from dotenv import load_dotenv

load_dotenv()

from src.model.model import RequestEvaluationBody
from src.service.thread import run_evaluation

from pkg.common.jobs import JobTracker
from pkg.common.logger import getLogger
from pkg.common.shutdown import install_sigterm_handler, run_until_stopped

stop = threading.Event()
tracker = JobTracker()


async def handle_message(body, logger):
    try:
        request_body = RequestEvaluationBody(**json.loads(body))

        logger.info(
            f"Received evaluation job {request_body.job_id}, "
            f"plugin={request_body.plugin}"
        )

        tracker.start(run_evaluation, args=(request_body,))

    except Exception as error:
        logger.error(f"Error processing evaluation message: {error}")


async def consume(queue, logger):
    async for message in queue:
        try:
            async with message.process():
                await handle_message(message.body.decode(), logger)
        except Exception as error:
            logger.error(f"Error processing evaluation message: {error}")


async def main(loop):
    logger = getLogger("EvaluationMockConsumer")
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    binding_key = "evaluation.mock"

    try:
        logger.info("Connecting to RabbitMQ")
        connection = await aio_pika.connect_robust(rabbitmq_url, loop=loop)
        logger.info("Connected to RabbitMQ")
    except Exception as error:
        logger.fatal(f"Error connecting to RabbitMQ: {error}")
        return

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        exchange = await channel.declare_exchange(
            "logs_topic",
            aio_pika.ExchangeType.TOPIC,
        )

        queue = await channel.declare_queue(
            "evaluation_mock_queue",
            exclusive=True,
        )

        await queue.bind(
            exchange,
            routing_key=binding_key,
        )

        logger.info("Consuming messages")

        if await run_until_stopped(consume(queue, logger), stop):
            logger.info("SIGTERM received - no longer taking new jobs")


RECONNECT_DELAY_SECONDS = 5

if __name__ == "__main__":
    install_sigterm_handler(stop)
    logger = getLogger("EvaluationMockSupervisor")

    while not stop.is_set():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(main(loop))
        except Exception as error:
            logger.error(f"Unexpected error from main(): {error}")
        finally:
            loop.close()

        if stop.is_set():
            break

        logger.info(f"main() exited - reconnecting in {RECONNECT_DELAY_SECONDS}s")
        stop.wait(RECONNECT_DELAY_SECONDS)

    logger.info(f"Waiting for {tracker.active()} running job(s) to finish")
    tracker.wait()
    logger.info("All jobs finished - exiting")
