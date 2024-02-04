import datetime

from pkg.common.publisher import publishJobStatusEvent, JobStatusEventMessage, JobUpdateData, Artifact
from src.const import MUTATION_BUCKET_NAME, MUTATION_SERVICE_NAME, MUTATION_STAGE_ID

def publishCompletedJobStatusToMQ(jobId, mutationId, mutationResult, ):
    message = JobStatusEventMessage(
        service_name=MUTATION_SERVICE_NAME,
        timestamp=datetime.datetime.now().isoformat(),
        data=JobUpdateData(
            job_id=jobId,
            mutation_id=mutationId,
            stage_id=MUTATION_STAGE_ID,
            status="COMPLETED",
            artifact=Artifact(bucket_name="", path=""),
            error="",
            mutation_result=mutationResult
        ),
    )
    publishJobStatusEvent(message)

def publishFailedJobStatusToMQ(job_id, mutationId, filePath, error):
    message = JobStatusEventMessage(
        service_name=MUTATION_SERVICE_NAME,
        timestamp=datetime.datetime.now().isoformat(),
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