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

from src.model.model import RequestBlastBody
from src.service.run_blast import runBlastThread
from pkg.common.logger import getLogger

async def handle_message(body, logger):
    logger.info("[x] Messaged Received")
    try:
        reqBody = RequestBlastBody(**json.loads(body))
        logger.info(f"Received message: {dict(reqBody)}")

        blastParam = reqBody.config
        blastParam.sequence = reqBody.input
        jobId = reqBody.job_id
        randomState = reqBody.config.random_state
        del blastParam.random_state

        blastThread = threading.Thread(
            target=runBlastThread, args=(blastParam, jobId, randomState)
        )
        blastThread.start()
    except Exception as e:
        logger.error(f"Error processing message: {e}")



async def main(loop):
    logger = getLogger("Consumer")
    conn_url = os.getenv("RABBITMQ_URL")

    try:
        connection = await aio_pika.connect_robust(conn_url, loop=loop)
        logger.info("Connected to RabbitMQ")
    except Exception as e:
        logger.fatal(f"Error connecting to RabbitMQ: {e}")
        return
    
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue("run_job.blast", durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await handle_message(message.body.decode(), logger)
                    logger.info("Message Processed")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()