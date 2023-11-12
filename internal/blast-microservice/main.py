from fastapi import FastAPI
import os

from dotenv import dotenv_values

import sys

sys.path.append("../")

import threading
import subprocess  # Import subprocess module

from src.model.model import RequestBody
from src.service.run_blast import run_blast_thread

from common.db import (
    createBucket,
    uploadToBucket,
    downloadFromBucket,
    asyncUploadToBucket,
)

# Replace with your actual Google Cloud Storage bucket name
# google_bucket = "gs://proteng_storage/"

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/createBucket")
def createBucketAPI():
    return createBucket("blast")


@app.get("/downloadFromBucket")
def downloadFromBucketAPI(bucketName, folderName, fileName):
    return downloadFromBucket(bucketName, folderName, fileName)


@app.post("/blast")
async def run_blast(requestBody: RequestBody):
    # Extract parameters from the request body
    blast_params = requestBody.blast_params
    job_id = requestBody.job_id
    running_id = requestBody.running_id
    random_state = requestBody.random_state

    # Create and start the BLAST thread using the function from the imported module
    blast_thread = threading.Thread(
        target=run_blast_thread, args=(blast_params, job_id, running_id, random_state)
    )
    blast_thread.start()

    return {"message": "Start BLAST"}
