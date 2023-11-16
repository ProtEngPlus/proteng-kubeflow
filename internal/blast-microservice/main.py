from fastapi import FastAPI
import os

from dotenv import dotenv_values

import sys

sys.path.append("../")

from dotenv import load_dotenv

load_dotenv()

import threading
import subprocess  # Import subprocess module

from src.model.model import RequestBody
from src.service.run_blast import run_blast_thread

from common.db import (
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
async def run_blast(requestBody: RequestBody):
    # Extract parameters from the request body
    blast_params = requestBody.blast_params
    job_id = requestBody.job_id
    random_state = requestBody.random_state
    try:
        # Create and start the BLAST thread using the function from the imported module
        blast_thread = threading.Thread(
            target=run_blast_thread, args=(blast_params, job_id, random_state)
        )
        blast_thread.start()

        return {"run_blast_thread": "success"}
    except:
        return {"run_blast_thread": "fail"}
