import threading
import sys
import os
import asyncio
import json
sys.path.append("../../")

import aio_pika
import aio_pika.abc
from dotenv import load_dotenv

load_dotenv()

from src.service.thread import runMutationThread
from src.model.model import RequestMutationBody
from pkg.common.logger import getLogger

async def handle_message(body, logger):
    logger.info("[x] Messaged Received")
    try:
        requestBody = RequestMutationBody(**json.loads(body))
        logger.info(f"[x] Received message: {requestBody.model_dump()}")

        mutationThread = threading.Thread(target=runMutationThread, args=(requestBody,))
        mutationThread.start()

    except Exception as e:
        logger.error(f"Error processing message: {e}")



async def main(loop):
    logger = getLogger("Consumer")
    conn_url = os.getenv("RABBITMQ_URL")
    queue_name = "run_job.mutation"

    try:
        logger.info("Connecting to RabbitMQ")
        connection = await aio_pika.connect_robust(conn_url, loop=loop)
        logger.info("Connected to RabbitMQ")
    except Exception as e:
        logger.fatal(f"Error connecting to RabbitMQ: {e}")
        return
    
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(queue_name, durable=True)

        logger.info("Consuming messages")
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await handle_message(message.body.decode(), logger)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()