from fastapi import FastAPI
import os

from dotenv import dotenv_values

import sys

sys.path.append("../")

from dotenv import load_dotenv

load_dotenv()

import threading
import subprocess  # Import subprocess module

from src.model.model import RequestBlastBody, BlastParams
from src.service.run_blast import runBlastThread

from pkg.common.db import (
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
    blastParams: BlastParams = requestBody.config
    blastParams.sequence = requestBody.input
    jobId = requestBody.job_id
    randomState = requestBody.config.random_state
    del blastParams.random_state
    try:
        # Create and start the BLAST thread using the function from the imported module
        blastThread = threading.Thread(
            target=runBlastThread, args=(blastParams, jobId, randomState)
        )
        blastThread.start()

        return {"run_blast_thread": "success"}
    except:
        return {"run_blast_thread": "fail"}
