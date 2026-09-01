import asyncio
import json
import os
import sys

import aio_pika

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

message = {
    "job_id": "local-test-1",
    "query_result_id": "local-test-1",
    "input": (
        "MLDDGNKLWYRDAIFYEVPVKSFYDSNGDGIGDFRGLTMKLGYLKNLGVDALWLLPFYKSPLKDDG"
        "YDISDYYSILPEYGTIDDFKQFIETAHSMNIRVIADLVLNHVSDQHPWFVEARKSRDSPKRNWFIW"
        "SDTPDKFKEARIIFIDTEKSNWAYDQESGQYYFHRFYSSQPDLNYDNPEVREEVKKIIRYWLNLGL"
        "DGFRADAVPYLF"
    ),
    "config": {
        "program": "blastp",
        "database": "nr",
        "expect": 10.0,
        "hitlist_size": 50,
        "perc_ident": 50,
        "hsp_cov": 99,
        "random_state": 2023,
        "seq_length": 300,
    },
    "meta": ["blast", "unirep", "ridgecv", "mutation"],
}


async def main():
    routing_key = sys.argv[1] if len(sys.argv) > 1 else "query.blast"

    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            "logs_topic", aio_pika.ExchangeType.TOPIC
        )
        await exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                content_type="text/plain",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=routing_key,
        )
        print(f"[x] sent job '{message['job_id']}' to routing key '{routing_key}'")


if __name__ == "__main__":
    asyncio.run(main())
