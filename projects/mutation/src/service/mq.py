import datetime

from src.const import MUTATION_SERVICE_NAME, MUTATION_STAGE_ID

from pkg.common.publisher import (
    Artifact,
    JobStatusEventMessage,
    JobUpdateData,
    publishJobStatusEvent,
)


def publishCompletedJobStatusToMQ(
    jobId,
    mutationId,
    mutationResult,
):
    message = JobStatusEventMessage(
        service_name=MUTATION_SERVICE_NAME,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        data=JobUpdateData(
            job_id=jobId,
            mutation_id=mutationId,
            stage_id=MUTATION_STAGE_ID,
            status="COMPLETED",
            artifact=Artifact(bucket_name="", path=""),
            error="",
            mutation_result=mutationResult,
        ),
    )
    publishJobStatusEvent(message)


def publishFailedJobStatusToMQ(job_id, mutationId, filePath, error):
    message = JobStatusEventMessage(
        service_name=MUTATION_SERVICE_NAME,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        data=JobUpdateData(
            job_id=job_id,
            mutation_id=mutationId,
            stage_id=MUTATION_STAGE_ID,
            status="FAILED",
            artifact=Artifact(bucket_name="", path=""),
            error=error,
        ),
    )
    publishJobStatusEvent(message)
