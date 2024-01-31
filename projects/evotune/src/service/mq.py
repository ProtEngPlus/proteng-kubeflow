import time

from pkg.common.publisher import publishJobStatusEvent, JobStatusEventMessage, JobUpdateData, Artifact
from src.const import EVOTUNE_SERVICE_NAME, EVOTUNE_BUCKET_NAME, EVOTUNE_STAGE_ID

def publishCompletedJobStatusToMQ(jobId, filePath):
    message = JobStatusEventMessage(
        service_name=EVOTUNE_SERVICE_NAME,
        timestamp=time.time(),
        data=JobUpdateData(
            job_id=jobId,
            stage_id=EVOTUNE_STAGE_ID,
            status="COMPLETED",
            artifact=Artifact(bucket_name=EVOTUNE_BUCKET_NAME, path=filePath),
            error="",
        ),
    )
    publishJobStatusEvent(message)

def publishFailedJobStatusToMQ(job_id, filePath, error):
    message = JobStatusEventMessage(
        service_name=EVOTUNE_SERVICE_NAME,
        timestamp=time.time(),
        data=JobUpdateData(
            job_id=job_id,
            stage_id=EVOTUNE_STAGE_ID,
            status="FAILED",
            artifact=Artifact(bucket_name=EVOTUNE_BUCKET_NAME, path=filePath),
            error=error,
        ),
    )
    publishJobStatusEvent(message)