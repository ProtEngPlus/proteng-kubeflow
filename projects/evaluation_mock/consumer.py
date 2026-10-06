import asyncio
import json
import os
import sys
import threading
import time

sys.path.append("../../")

import aio_pika
from dotenv import load_dotenv

load_dotenv()

from pkg.common.logger import getLogger
from src.model.model import RequestEvaluationBody
from src.service.thread import run_evaluation


async def handle_message(body, logger):
    try:
        request_body = RequestEvaluationBody(**json.loads(body))

        logger.info(
            f"Received evaluation job {request_body.job_id}, "
            f"plugin={request_body.plugin}"
        )

        evaluation_thread = threading.Thread(
            target=run_evaluation,
            args=(request_body,),
        )
        evaluation_thread.start()

    except Exception as error:
        logger.error(f"Error processing evaluation message: {error}")


async def main(loop):
    logger = getLogger("EvaluationMockConsumer")
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    binding_key = "evaluation.mock"

    connection = await aio_pika.connect_robust(
        rabbitmq_url,
        loop=loop,
    )

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

        logger.info("Waiting for evaluation.mock messages")

        async for message in queue:
            async with message.process():
                await handle_message(
                    message.body.decode(),
                    logger,
                )


RECONNECT_DELAY_SECONDS = 5

if __name__ == "__main__":
    logger = getLogger("EvaluationMockSupervisor")

    while True:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(main(loop))
        except Exception as error:
            logger.error(error)
        finally:
            loop.close()

        time.sleep(RECONNECT_DELAY_SECONDS)
