from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
import threading
import sys
import logging
import os
sys.path.append("../../")

from dotenv import load_dotenv
load_dotenv()

from src.model.model import RequestFitTopBody
from src.service.run_top_model import doFitTop

logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG") == "true" else logging.INFO)

app = FastAPI()

@app.exception_handler(HTTPException)
def http_exception_handler(req, e):
    return JSONResponse({"code": 500, "error": str(e)}, 500)

@app.get("/")
async def root():
    return {"message": "Hello World"}   

@app.post("/top-model")
def requestTopModel(requestBody: RequestFitTopBody):
    try:
        # Create and start the BLAST thread
        topModelThread = threading.Thread(target=doFitTop, args=(requestBody,))
        topModelThread.start()

        return {"code": 200, "message": "started fittop thread"}
    except Exception as e:
        raise e
    
