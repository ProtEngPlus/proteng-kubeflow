
import threading
import sys
sys.path.append("../")

from fastapi import FastAPI
from aiofile import AIOFile

from src.model.model import RequestEvotuneBody
from src.service.train import runEvotuneThread

from common.db import createBucket, uploadToBucket, downloadFromBucket, asyncUploadToBucket

app = FastAPI()

@app.get("/test")
async def read_root():
    async with AIOFile("./src/data/example_data.txt", mode="r") as afp:
        f = await afp.read()
        url = asyncUploadToBucket("unirep", "test", "test.txt", f)
        return url
    
@app.get("/createBucket")
def createBucketAPI():
    return createBucket("unirep")

@app.get("/uploadToBucket")
def uploadToBucketAPI():
    return uploadToBucket("unirep", "test", "test.txt", "test")

@app.get("/downloadFromBucket")
def downloadFromBucketAPI():
    return downloadFromBucket("unirep", "test", "test.txt")

@app.post("/evotune")
def requestEvotune(requestBody: RequestEvotuneBody):
    print("----------------------------------------------------------")
    print("requesting evotune service...")
    print(requestBody)
    try:
        # Create and start the BLAST thread
        evotuneThread = threading.Thread(target=runEvotuneThread, args=(requestBody,))
        evotuneThread.start()

        return {"run_evotune_thread":"success"}
    except:
        return {"run_evotune_thread":"fail"}