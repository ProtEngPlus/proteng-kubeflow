import asyncio
import json
import os
import sys
import threading
import time

sys.path.append("../../")

import aio_pika
import aio_pika.abc
from dotenv import load_dotenv

load_dotenv()

from src.model.model import RequestFitTopBody
from src.service.run_top_model import doFitTop

from pkg.common.logger import getLogger


async def handle_message(body, logger):
    logger.info("[x] Messaged Received")
    try:
        requestBody = RequestFitTopBody(**json.loads(body))
        logger.info(f"[x] Received message: {requestBody.dict()}")

        topModelThread = threading.Thread(target=doFitTop, args=(requestBody,))
        topModelThread.start()

    except Exception as e:  # noqa: BLE001 -- must stay alive on bad messages
        logger.error(f"Error processing message: {e}")


async def main(loop):
    logger = getLogger("Consumer")
    conn_url = os.getenv("RABBITMQ_URL")
    binding_key = "fittop.ridgecv"

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

        queue = await channel.declare_queue("fittop_queue", exclusive=True)
        await queue.bind(exchange, routing_key=binding_key)

        logger.info("Consuming messages")

        async for message in queue:
            try:
                async with message.process():
                    await handle_message(message.body.decode(), logger)
            except Exception as e:  # noqa: BLE001 -- must stay alive on bad messages
                logger.error(f"Error processing message: {e}")


RECONNECT_DELAY_SECONDS = 5
if __name__ == "__main__":
    supervisorLogger = getLogger("Supervisor")
    while True:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main(loop))
        except Exception as e:  # noqa: BLE001 -- retry forever
            supervisorLogger.error(f"Unexpected error from main(): {e}")
        finally:
            loop.close()
        supervisorLogger.info(
            f"main() exited - reconnecting in {RECONNECT_DELAY_SECONDS}s"
        )
        time.sleep(RECONNECT_DELAY_SECONDS)
