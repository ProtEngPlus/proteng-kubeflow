import threading
import sys

sys.path.append("../../")
from dotenv import load_dotenv

load_dotenv()

import os

# silence TQDM
if not os.getenv("DEBUG") == "true":
    os.environ["TQDM_DISABLE"] = "1"

from fastapi import FastAPI, APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from src.logger import evotuneLogger as logger
from src.model.model import RequestEvotuneBody
from src.service.thread import runEvotuneThread
from pkg.common.fast_api import GetLoggingRouteClass
from pkg.common.logger import getLogger

app = FastAPI()
router = APIRouter(route_class=GetLoggingRouteClass(getLogger("FastAPI")))


@app.exception_handler(HTTPException)
def http_exception_handler(req, e):
    return JSONResponse({"code": 500, "error": str(e)}, 500)


@router.post("/evotune_ESM")
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


app.include_router(router)
