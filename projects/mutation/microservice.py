import threading
import sys
import os
import logging
sys.path.append("../../")
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from src.service.thread import runMutationThread
from src.model.model import RequestMutationBody

logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG") == "true" else logging.INFO)

app = FastAPI()

@app.exception_handler(HTTPException)
def http_exception_handler(req, e):
    return JSONResponse({"code": 500, "error": str(e)}, 500)

@app.post("/mutation")
def requestEvotune(requestBody: RequestMutationBody):
    logging.debug("----------------------------------------------------------")
    logging.debug("requesting mutation service...")
    logging.debug(requestBody)
    try:
        # Create and start the MUTATION thread
        mutationThread = threading.Thread(target=runMutationThread, args=(requestBody,))
        mutationThread.start()
        
        return {"code": 200, "message": "started mutation thread"}
    except Exception as e:
        raise e