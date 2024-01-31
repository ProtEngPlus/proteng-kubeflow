import threading
import sys
sys.path.append("../../")
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from pkg.common.db import createBucket, downloadFromBucket, uploadToBucket
from src.model.model import RequestEvotuneBody, RequestBucketBody
from src.service.thread import runEvotuneThread

app = FastAPI()

@app.exception_handler(HTTPException)
def http_exception_handler(req, e):
    return JSONResponse({"code": 500, "error": str(e)}, 500)

@app.post("/createBucket")
def bucketCreation(requestBody: RequestBucketBody):
    print("----------------------------------------------------------")
    print("creating bucket...")
    createBucket(requestBody.bucket_name)
    print("bucket created")
    return "success"

@app.post("/downloadFromBucket")
def bucketDownload(requestBody: RequestBucketBody):
    print("----------------------------------------------------------")
    print("downloading from bucket...")
    print(downloadFromBucket(requestBody.bucket_name, requestBody.file_name))
    print("downloaded")
    return "success"

@app.post("/uploadToBucket")
def bucketUpload(requestBody: RequestBucketBody):
    print("----------------------------------------------------------")
    print("uploading to bucket...")
    uploadToBucket(requestBody.bucket_name, requestBody.file_name, requestBody.file)
    print("uploaded")
    return "success"

@app.post("/evotune")
def requestEvotune(requestBody: RequestEvotuneBody):
    print("----------------------------------------------------------")
    print("requesting evotune service...")
    print(requestBody)
    try:
        # Create and start the EVOTUNE thread
        evotuneThread = threading.Thread(target=runEvotuneThread, args=(requestBody,))
        evotuneThread.start()

        return {"code": 200, "message": "started evotune thread"}
    except Exception as e:
        raise e