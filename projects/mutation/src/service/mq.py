import time

from pkg.common.publisher import publishJobStatusEvent, JobStatusEventMessage, JobUpdateData, Artifact
from src.const import MUTATION_BUCKET_NAME, MUTATION_SERVICE_NAME, MUTATION_STAGE_ID

def publishCompletedJobStatusToMQ(jobId, mutationResult):
    message = JobStatusEventMessage(
        service_name=MUTATION_SERVICE_NAME,
        timestamp=time.time(),
        data=JobUpdateData(
            job_id=jobId,
            stage_id=MUTATION_STAGE_ID,
            status="COMPLETED",
            artifact=Artifact(bucket_name="", path=""),
            error="",
            mutation_result=mutationResult
        ),
    )
    publishJobStatusEvent(message)

def publishFailedJobStatusToMQ(job_id, filePath, error):
    message = JobStatusEventMessage(
        service_name=MUTATION_SERVICE_NAME,
        timestamp=time.time(),
        data=JobUpdateData(
            job_id=job_id,
            stage_id=MUTATION_STAGE_ID,
            status="FAILED",
            artifact=Artifact(bucket_name="", path=""),
            error=error,
        ),
    )
    publishJobStatusEvent(message)