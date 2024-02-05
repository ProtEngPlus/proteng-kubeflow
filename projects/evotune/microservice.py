import threading
import sys
import logging
sys.path.append("../../")
from dotenv import load_dotenv
import os
load_dotenv()

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from pkg.common.db import createBucket, downloadFromBucket, uploadToBucket
from src.model.model import RequestEvotuneBody, RequestBucketBody
from src.service.thread import runEvotuneThread

logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG") == "true" else logging.INFO)

app = FastAPI()

@app.exception_handler(HTTPException)
def http_exception_handler(req, e):
    return JSONResponse({"code": 500, "error": str(e)}, 500)

@app.post("/createBucket")
def bucketCreation(requestBody: RequestBucketBody):
    logging.debug("----------------------------------------------------------")
    logging.debug("creating bucket...")
    createBucket(requestBody.bucket_name)
    logging.debug("bucket created")
    return "success"

@app.post("/downloadFromBucket")
def bucketDownload(requestBody: RequestBucketBody):
    logging.debug("----------------------------------------------------------")
    logging.debug("downloading from bucket...")
    logging.debug(downloadFromBucket(requestBody.bucket_name, requestBody.file_name))
    logging.debug("downloaded")
    return "success"

@app.post("/uploadToBucket")
def bucketUpload(requestBody: RequestBucketBody):
    logging.debug("----------------------------------------------------------")
    logging.debug("uploading to bucket...")
    uploadToBucket(requestBody.bucket_name, requestBody.file_name, requestBody.file)
    logging.debug("uploaded")
    return "success"

@app.post("/evotune")
def requestEvotune(requestBody: RequestEvotuneBody):
    logging.debug("----------------------------------------------------------")
    logging.debug("requesting evotune service...")
    logging.debug(requestBody)
    try:
        # Create and start the EVOTUNE thread
        evotuneThread = threading.Thread(target=runEvotuneThread, args=(requestBody,))
        evotuneThread.start()

        return {"code": 200, "message": "started evotune thread"}
    except Exception as e:
        raise e