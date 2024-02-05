import threading
import sys
sys.path.append("../../")
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from pkg.common.db import createBucket, downloadFromBucket, uploadToBucket
from pkg.common.logger import getLogger
from src.model.model import RequestEvotuneBody, RequestBucketBody
from src.service.thread import runEvotuneThread

logger = getLogger("evotune_service")

app = FastAPI()

@app.exception_handler(HTTPException)
def http_exception_handler(req, e):
    return JSONResponse({"code": 500, "error": str(e)}, 500)

@app.post("/createBucket")
def bucketCreation(requestBody: RequestBucketBody):
    logger.debug("----------------------------------------------------------")
    logger.debug("creating bucket...")
    createBucket(requestBody.bucket_name)
    logger.debug("bucket created")
    return "success"

@app.post("/downloadFromBucket")
def bucketDownload(requestBody: RequestBucketBody):
    logger.debug("----------------------------------------------------------")
    logger.debug("downloading from bucket...")
    logger.debug(downloadFromBucket(requestBody.bucket_name, requestBody.file_name))
    logger.debug("downloaded")
    return "success"

@app.post("/uploadToBucket")
def bucketUpload(requestBody: RequestBucketBody):
    logger.debug("----------------------------------------------------------")
    logger.debug("uploading to bucket...")
    uploadToBucket(requestBody.bucket_name, requestBody.file_name, requestBody.file)
    logger.debug("uploaded")
    return "success"

@app.post("/evotune")
def requestEvotune(requestBody: RequestEvotuneBody):
    logger.debug("----------------------------------------------------------")
    logger.debug("requesting evotune service...")
    logger.debug(requestBody)
    try:
        # Create and start the EVOTUNE thread
        evotuneThread = threading.Thread(target=runEvotuneThread, args=(requestBody,))
        evotuneThread.start()

        return {"code": 200, "message": "started evotune thread"}
    except Exception as e:
        raise e