import sys
import threading

sys.path.append("../../")
from dotenv import load_dotenv

load_dotenv()

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from src.logger import mutationLogger as logger
from src.model.model import RequestMutationBody
from src.service.thread import runMutationThread

from pkg.common.fast_api import GetLoggingRouteClass
from pkg.common.logger import getLogger

app = FastAPI()
router = APIRouter(route_class=GetLoggingRouteClass(getLogger("FastAPI")))


@app.exception_handler(HTTPException)
def http_exception_handler(req, e):
    return JSONResponse({"code": 500, "error": str(e)}, 500)


@router.post("/mutation")
def requestEvotune(requestBody: RequestMutationBody):
    logger.debug("----------------------------------------------------------")
    logger.debug("requesting mutation service...")
    logger.debug(requestBody)
    # Create and start the MUTATION thread
    mutationThread = threading.Thread(target=runMutationThread, args=(requestBody,))
    mutationThread.start()

    return {"code": 200, "message": "started mutation thread"}


app.include_router(router)
