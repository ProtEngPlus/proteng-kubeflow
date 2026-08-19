import json

import pika


def main():
    connection = pika.BlockingConnection(
        pika.URLParameters("amqp://admin:pass@localhost:5672/")
    )
    channel = connection.channel()

    # edit queue name here
    queue_name = "run_job.blast"

    channel.exchange_declare(queue_name, durable=True)

    channel.queue_declare(
        queue=queue_name,
        durable=True,
    )
    channel.queue_bind(exchange=queue_name, queue=queue_name, routing_key=queue_name)

    # edit job request body here
    message = {
        "job_id": "204",
        "input": "MLDDGNKLWYRDAIFYEVPVKSFYDSNGDGIGDFRGLTMKLGYLKNLGVDALWLLPFYKSPLKDDGYDISDYYSILPEYGTIDDFKQFIETAHSMNIRVIADLVLNHVSDQHPWFVEARKSRDSPKRNWFIWSDTPDKFKEARIIFIDTEKSNWAYDQESGQYYFHRFYSSQPDLNYDNPEVREEVKKIIRYWLNLGLDGFRADAVPYLFKREGTNCENLPETHNFFKEIRKMMDSEYPGTILLAEANQWPTDARAYFGNGDEFHMAFNFPLMPRIFIALAKRDYYPIEDIINQTLPVPDNCDWCTFLRNHDELTLEMVTDAERDIMFREYAKLPKMRLNLGIRRRLAPLVDNDINTIELLNALIFSLPGTPIIYYGDEIGMGDNIYLGDRNGVRTPMQWSYDRNAGFSTADSEELYSPVITNPNYNYESVNVEAEMRLNSSLLKWMIKIINIRKDYKELLGRGSIKFINQKNKRVLVYIREYENQRMLCLFNLSRSPTYVELDLHEYAGLKPIEAITKAAFPRIGDLNYFITMTPRSFFWFNLIVPERDDSFDLVDDYDQS",
        "config": {
            "program": "blastp",
            "database": "nr",
            "expect": 10.0,
            "hitlist_size": 10000,
            "perc_ident": 50,
            "hsp_cov": 99,
            "random_state": 2023,
        },
        "meta": ["blast", "unirep", "ridgecv", "mutation"],
    }

    message = json.dumps(message)
    channel.basic_publish(
        exchange=queue_name,
        routing_key=queue_name,
        body=message,
        properties=pika.BasicProperties(content_type="text/plain", delivery_mode=2),
    )
    print(f"[x] Sent '{message}'")

    connection.close()


if __name__ == "__main__":
    main()
