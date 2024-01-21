from fastapi import FastAPI
import os

from dotenv import load_dotenv

load_dotenv()

import threading
import subprocess  # Import subprocess module

from modules.blast.model.model import RequestBlastBody, BlastParams
from modules.blast.service.run_blast import run_blast_thread

from modules.common.db import (
    createBucket,
    uploadToBucket,
    downloadFromBucket,
)


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/createBucket")
def createBucketAPI(bucketName):
    createBucket(bucketName)
    return "success"


@app.get("/downloadFromBucket")
def downloadFromBucketAPI(bucketName, fileName):
    s = downloadFromBucket(bucketName, fileName)
    print(s)


@app.post("/blast")
async def run_blast(requestBody: RequestBlastBody):
    # Extract parameters from the request body
    blast_params: BlastParams = requestBody.config
    blast_params.sequence = requestBody.input
    job_id = requestBody.job_id
    random_state = requestBody.config.randomstate
    del blast_params.randomstate
    try:
        # Create and start the BLAST thread using the function from the imported module
        blast_thread = threading.Thread(
            target=run_blast_thread, args=(blast_params, job_id, random_state)
        )
        blast_thread.start()

        return {"run_blast_thread": "success"}
    except:
        return {"run_blast_thread": "fail"}
