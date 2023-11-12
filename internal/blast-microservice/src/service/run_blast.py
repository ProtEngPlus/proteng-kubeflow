from Bio.Blast import NCBIWWW
import re
import pandas as pd
import threading
import json
from common.db import (
    createBucket,
    uploadToBucket,
    downloadFromBucket,
    asyncUploadToBucket,
)


def run_blast_thread(blast_params, job_id, running_id, random_state):
    print("Start BLAST")  # Print the "start blast" message when the thread starts

    # Run BLAST
    blast_args = {k: v for k, v in blast_params.dict().items() if v is not None}
    result_handle = NCBIWWW.qblast(**blast_args)
    result = result_handle.read()

    sequences = re.findall(r"<Hsp_hseq>(.*?)</Hsp_hseq>", result)
    scores = re.findall(r"<Hsp_score>(.*?)</Hsp_score>", result)

    data = {"sequences": sequences, "score": scores}
    df = pd.DataFrame(data)

    # Split the dataframe
    out_domain_val_set = df.sample(frac=0.1, weights="score", random_state=random_state)
    train_set = df.drop(out_domain_val_set.index)

    out_domain_val_set = out_domain_val_set["sequences"].tolist()
    train_set = train_set["sequences"].tolist()

    # Create a dictionary to store the results
    results = {
        "Train Set": train_set,
        "Out Domain Validation Set": out_domain_val_set,
    }

    # Convert the results to a JSON string
    results_json = json.dumps(results)

    # Upload the JSON string directly to the object storage bucket
    upload_status = uploadToBucket("sequence", job_id, running_id, results_json)

    print("Thread finished")  # Print "Thread finished" when the thread is done
    return upload_status
