from fastapi import FastAPI, APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

import sys

sys.path.append("../../")

from dotenv import load_dotenv

load_dotenv()

import threading

from src.model.model import RequestBlastBody, BlastParams
from src.service.run_blast import runBlastThread
from pkg.common.fast_api import GetLoggingRouteClass
from pkg.common.logger import getLogger

app = FastAPI()
router = APIRouter(route_class=GetLoggingRouteClass(getLogger("FastAPI")))


@app.exception_handler(HTTPException)
def http_exception_handler(req, e):
    return JSONResponse({"code": 500, "error": str(e)}, 500)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@router.post("/blast")
async def run_blast(requestBody: RequestBlastBody):
    # Extract parameters from the request body
    blastParams: BlastParams = requestBody.config
    blastParams.sequence = requestBody.input
    jobId = requestBody.job_id
    randomState = requestBody.config.random_state
    del blastParams.random_state
    try:
        # Create and start the BLAST thread using the function from the imported module
        blastThread = threading.Thread(
            target=runBlastThread, args=(blastParams, jobId, randomState)
        )
        blastThread.start()

        return {"code": 200, "message": "started blast thread"}
    except Exception as e:
        raise e


app.include_router(router)
