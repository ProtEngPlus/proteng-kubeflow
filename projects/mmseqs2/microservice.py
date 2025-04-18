from fastapi import FastAPI, APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

import sys
sys.path.append("../../")

from dotenv import load_dotenv

load_dotenv()

import threading
import subprocess  # Import subprocess module

from src.model.model import RequestMMseqs2Body, MMseqs2Params
from src.service.run_mmseqs2 import runMMseqs2Thread
from pkg.common.fast_api import GetLoggingRouteClass
from pkg.common.logger import getLogger

app = FastAPI()
router = APIRouter(route_class=GetLoggingRouteClass(getLogger('FastAPI')))

@app.exception_handler(HTTPException)
def http_exception_handler(req, e):
    return JSONResponse({"code": 500, "error": str(e)}, 500)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@router.post("/mmseqs2")
async def run_mmseqs2(requestBody: RequestMMseqs2Body):
    # Extract parameters from the request body
    mmseqs2Params: MMseqs2Params = requestBody.config
    mmseqs2Params.sequence = requestBody.input
    jobId = requestBody.job_id
    randomState = requestBody.config.random_state
    del mmseqs2Params.random_state
    try:
        # Create and start the MMseqs2 thread using the function from the imported module
        mmseqs2Thread = threading.Thread(
            target=runMMseqs2Thread, args=(mmseqs2Params, jobId, randomState)
        )
        mmseqs2Thread.start()

        return {"code": 200, "message": "started mmseqs2 thread"}
    except Exception as e:
        raise e
    
app.include_router(router)
