from Bio.Blast import NCBIWWW
import re
import pandas as pd
import threading
import json
from common.db import createBucket, uploadToBucket, downloadFromBucket
from common.publisher import *
from datetime import datetime, timezone
import time


def runBlastThread(blastParams, jobId, randomState):
    try:
        print(
            "Start BLAST Thread"
        )  # Print the "start blast" message when the thread starts

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

        print("saving...")
        # Upload the JSON string directly to the object storage bucket
        upload_status = uploadToBucket("similar_protein", jobId, resultsJson)
        print(upload_status)

        message = JobStatusEventMessage(
            service_name="blast-microservice",
            timestamp=time.time(),
            data=JobUpdateData(
                job_id=jobId,
                stage_id=0,
                status="COMPLETED",
                artifact=Artifact(bucket_name="similar_protein", path=jobId),
            ),
        )
        publishJobStatusEvent(message)
        print("Thread finished")
    except Exception as err:
        # TODO: Send Error Message to Message Queue
        message = JobStatusEventMessage(
            service_name="blast-microservice",
            timestamp=time.time(),
            data=JobUpdateData(
                job_id=jobId,
                stage_id=0,
                status="FAILED",
                artifact=Artifact(bucket_name="similar_protein", path=jobId),
                error=str(err),
            ),
        )
        publishJobStatusEvent(message)
        print(f"Unexpected {err=}, {type(err)=}")
