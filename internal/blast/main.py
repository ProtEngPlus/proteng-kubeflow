from fastapi import FastAPI
import os

from dotenv import dotenv_values

import threading
import subprocess  # Import subprocess module

from src.model.model import RequestBody
from src.service.run_blast import run_blast_thread

# Replace with your actual Google Cloud Storage bucket name
# google_bucket = "gs://proteng_storage/"

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/blast")
async def run_blast(requestBody: RequestBody):
    # Extract parameters from the request body
    blast_params = requestBody.blast_params
    job_id = requestBody.job_id
    random_state = requestBody.random_state

    # Create and start the BLAST thread using the function from the imported module
    blast_thread = threading.Thread(
        target=run_blast_thread, args=(blast_params, job_id, random_state)
    )
    blast_thread.start()

    return {"message": "Start BLAST"}
