import asyncio
import json
import os
import sys
import threading

sys.path.append("../../")

import aio_pika
import aio_pika.abc
from dotenv import load_dotenv

load_dotenv()

from src.model.model import RequestMMseqs2Body
from src.service.run_mmseqs2 import runMMseqs2Thread

from pkg.common.logger import getLogger


async def handle_message(body, logger):
    logger.info("[x] Messaged Received")
    try:
        requestBody = RequestMMseqs2Body(**json.loads(body))
        logger.info(f"[x] Received message: {requestBody.dict()}")

        mmseqs2Param = requestBody.config
        mmseqs2Param.sequence = requestBody.input
        jobId = requestBody.job_id
        queryResultId = requestBody.query_result_id
        randomState = requestBody.config.random_state
        del mmseqs2Param.random_state

        mmseqs2Thread = threading.Thread(
            target=runMMseqs2Thread,
            args=(mmseqs2Param, jobId, queryResultId, randomState),
        )
        mmseqs2Thread.start()

    except Exception as e:  # noqa: BLE001 -- must stay alive on bad messages
        logger.error(f"Error processing message: {e}")


async def main(loop):
    logger = getLogger("Consumer")
    conn_url = os.getenv("RABBITMQ_URL")
    binding_key = "query.mmseqs2"

    try:
        logger.info("Connecting to RabbitMQ")
        connection = await aio_pika.connect_robust(conn_url, loop=loop)
        logger.info("Connected to RabbitMQ")
    except Exception as e:  # noqa: BLE001 -- exit cleanly on connect failure
        logger.fatal(f"Error connecting to RabbitMQ: {e}")
        return

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        exchange = await channel.declare_exchange(
            "logs_topic", aio_pika.ExchangeType.TOPIC
        )

        queue = await channel.declare_queue("mmseqs2_queue", exclusive=True)
        await queue.bind(exchange, routing_key=binding_key)

        logger.info("Consuming messages")

        async for message in queue:
            try:
                async with message.process():
                    await handle_message(message.body.decode(), logger)
            except Exception as e:  # noqa: BLE001 -- must stay alive on bad messages
                logger.error(f"Error processing message: {e}")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(loop))
    loop.close()
