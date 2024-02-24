from Bio.Blast import NCBIWWW
import re
import pandas as pd
import threading
import json
from pkg.common.db import createBucket, uploadToBucket, downloadFromBucket
from pkg.common.publisher import *
from datetime import datetime, timezone
import datetime
from src.logger import blastLogger as logger

def runBlastThread(blastParams, jobId, randomState):
    try:
        logger.info(f"job id {jobId}: Running BLAST")
        # Run BLAST
        blastArgs = {k: v for k, v in blastParams.dict().items() if v is not None}
        resultHandle = NCBIWWW.qblast(**blastArgs)
        result = resultHandle.read()

        sequences = re.findall(r"<Hsp_hseq>(.*?)</Hsp_hseq>", result)
        scores = re.findall(r"<Hsp_score>(.*?)</Hsp_score>", result)

        data = {"sequences": sequences, "score": scores}
        df = pd.DataFrame(data)

        # Split the dataframe
        outDomainValSet = df.sample(frac=0.1, weights="score", random_state=randomState)
        trainSet = df.drop(outDomainValSet.index)

        outDomainValSet = outDomainValSet["sequences"].tolist()
        trainSet = trainSet["sequences"].tolist()

        # Create a dictionary to store the results
        results = {
            "train_set": trainSet,
            "out_domain_val_set": outDomainValSet,
        }
        # Convert the results to a JSON string
        resultsJson = json.dumps(results)

        logger.info(f"job id {jobId}: Uploading results to object storage")
        # Upload the JSON string directly to the object storage bucket
        upload_status = uploadToBucket("similar_protein", jobId, resultsJson)
        logger.info(f"job id {jobId}: Upload status: {upload_status}")

        message = JobStatusEventMessage(
            service_name="blast-microservice",
            timestamp=datetime.datetime.now().isoformat(),
            data=JobUpdateData(
                job_id=jobId,
                stage_id=0,
                status="COMPLETED",
                artifact=Artifact(bucket_name="similar_protein", path=jobId),
            ),
        )
        publishJobStatusEvent(message)
        logger.info(f"Job {jobId} completed successfully")
    except Exception as err:
        logger.error(f"job id {jobId}: error run blast: Unexpected {err=}, {type(err)=}")
        message = JobStatusEventMessage(
            service_name="blast-microservice",
            timestamp=datetime.datetime.now().isoformat(),
            data=JobUpdateData(
                job_id=jobId,
                stage_id=0,
                status="FAILED",
                artifact=Artifact(bucket_name="similar_protein", path=jobId),
                error=str(err),
            ),
        )
        publishJobStatusEvent(message)
