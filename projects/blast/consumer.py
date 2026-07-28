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
        requestBody = RequestBlastBody(**json.loads(body))
        logger.info(f"[x] Received message: {requestBody.dict()}")

        blastParam = requestBody.config
        blastParam.sequence = requestBody.input
        jobId = requestBody.job_id
        queryResultId = requestBody.query_result_id
        randomState = requestBody.config.random_state
        del blastParam.random_state

        blastThread = threading.Thread(
            target=runBlastThread, args=(blastParam, jobId, queryResultId, randomState)
        )
        blastThread.start()

    except Exception as e:
        logger.error(f"Error processing message: {e}")



async def main(loop):
    logger = getLogger("Consumer")
    conn_url = os.getenv("RABBITMQ_URL")
    binding_key = "query.blast"

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
        
        exchange = await channel.declare_exchange("logs_topic", aio_pika.ExchangeType.TOPIC)

        queue = await channel.declare_queue("blast_queue", exclusive=True)
        await queue.bind(exchange, routing_key=binding_key)
        
        logger.info("Consuming messages")
        
        async for message in queue:
            try:
                async with message.process():
                    await handle_message(message.body.decode(), logger)
            except Exception as e:
                logger.error(f"Error processing message: {e}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(loop))
    loop.close()