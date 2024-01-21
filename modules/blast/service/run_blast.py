from Bio.Blast import NCBIWWW
import re
import pandas as pd
import threading
import json
from modules.common.db import createBucket, uploadToBucket, downloadFromBucket
from modules.common.publisher import *
from datetime import datetime, timezone


def run_blast_thread(blast_params, job_id, random_state):
    try:
        print(
            "Start BLAST Thread"
        )  # Print the "start blast" message when the thread starts

        # Run BLAST
        blast_args = {k: v for k, v in blast_params.dict().items() if v is not None}
        result_handle = NCBIWWW.qblast(**blast_args)
        result = result_handle.read()

        sequences = re.findall(r"<Hsp_hseq>(.*?)</Hsp_hseq>", result)
        scores = re.findall(r"<Hsp_score>(.*?)</Hsp_score>", result)

        data = {"sequences": sequences, "score": scores}
        df = pd.DataFrame(data)

        # Split the dataframe
        out_domain_val_set = df.sample(
            frac=0.1, weights="score", random_state=random_state
        )
        train_set = df.drop(out_domain_val_set.index)

        out_domain_val_set = out_domain_val_set["sequences"].tolist()
        train_set = train_set["sequences"].tolist()

        # Create a dictionary to store the results
        results = {
            "train_set": train_set,
            "out_domain_val_set": out_domain_val_set,
        }
        # Convert the results to a JSON string
        results_json = json.dumps(results)

        print("saving...")
        # Upload the JSON string directly to the object storage bucket
        upload_status = uploadToBucket("similar_protein", job_id, results_json)
        print(upload_status)

        current_time = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

        message = JobStatusEventMessage(
            service_name="blast-microservice",
            timestamp=current_time,
            data=JobUpdateData(
                job_id=job_id,
                stage_id=0,
                status="COMPLETED",
                artifact=Artifact(bucket_name="similar_protein", path=job_id),
            ),
        )
        publishJobStatusEvent(message)
        print("Thread finished")
    except Exception as err:
        # TODO: Send Error Message to Message Queue
        current_time = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
        message = JobStatusEventMessage(
            service_name="blast-microservice",
            timestamp=current_time,
            data=JobUpdateData(
                job_id=job_id,
                stage_id=0,
                status="FAILED",
                artifact=Artifact(bucket_name="similar_protein", path=job_id),
                error=str(err),
            ),
        )
        publishJobStatusEvent(message)
        print(f"Unexpected {err=}, {type(err)=}")
