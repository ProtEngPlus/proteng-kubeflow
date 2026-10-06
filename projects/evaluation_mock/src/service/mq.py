import datetime
import json
import os

from pkg.common.publisher import publishDefaultExchange
from src.const import EVALUATION_SERVICE_NAME, EVALUATION_STAGE_ID


def publish_completed(request_body, results):
    message = {
        "service_name": EVALUATION_SERVICE_NAME,
        "timestamp": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        "data": {
            "job_id": request_body.job_id,
            "stage_id": EVALUATION_STAGE_ID,
            "status": "COMPLETED",
            "evaluation_run_id": request_body.evaluation_run_id,
            "plugin": request_body.plugin,
            "evaluation_results": results,
            "error": "",
        },
    }

    publishDefaultExchange(
        os.environ["RABBITMQ_URL"],
        "job_status_event",
        json.dumps(message),
    )


def publish_failed(request_body, error):
    message = {
        "service_name": EVALUATION_SERVICE_NAME,
        "timestamp": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        "data": {
            "job_id": request_body.job_id,
            "stage_id": EVALUATION_STAGE_ID,
            "status": "FAILED",
            "evaluation_run_id": request_body.evaluation_run_id,
            "plugin": request_body.plugin,
            "evaluation_results": [],
            "error": str(error),
        },
    }

    publishDefaultExchange(
        os.environ["RABBITMQ_URL"],
        "job_status_event",
        json.dumps(message),
    )
