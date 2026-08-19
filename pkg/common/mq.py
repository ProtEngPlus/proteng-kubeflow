import datetime

from pkg.common.publisher import (
    Artifact,
    JobStatusEventMessage,
    JobUpdateData,
    publishJobStatusEvent,
)


def publishCompletedJobStatusToMQ(serviceName, bucketName, stageID, jobId, filePath):
    message = JobStatusEventMessage(
        service_name=serviceName,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        data=JobUpdateData(
            job_id=jobId,
            stage_id=stageID,
            status="COMPLETED",
            artifact=Artifact(bucket_name=bucketName, path=filePath),
            error="",
        ),
    )
    publishJobStatusEvent(message)


def publishFailedJobStatusToMQ(
    serviceName, bucketName, stageID, job_id, filePath, error
):
    message = JobStatusEventMessage(
        service_name=serviceName,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        data=JobUpdateData(
            job_id=job_id,
            stage_id=stageID,
            status="FAILED",
            artifact=Artifact(bucket_name=bucketName, path=filePath),
            error=error,
        ),
    )
    publishJobStatusEvent(message)
