import threading
import sys
sys.path.append("../")
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

from common.db import createBucket, downloadFromBucket
from src.model.model import RequestEvotuneBody
from src.service.train import runEvotuneThread

app = FastAPI()

@app.get("/createBucket")
def bucketCreation():
    print("----------------------------------------------------------")
    print("creating bucket...")
    createBucket("unirep")
    print("bucket created")
    return "success"

@app.get("/evotune")
def get_weights():
    print("----------------------------------------------------------")
    print("getting evotuned_params...")
    print(downloadFromBucket("unirep", "123", "1.pkl"))
    print("evotuned_params downloaded")
    return "success"

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