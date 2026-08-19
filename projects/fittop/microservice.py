import sys
import threading

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

sys.path.append("../../")

from dotenv import load_dotenv

load_dotenv()

from src.model.model import RequestFitTopBody
from src.service.run_top_model import doFitTop

from pkg.common.fast_api import GetLoggingRouteClass
from pkg.common.logger import getLogger

app = FastAPI()
router = APIRouter(route_class=GetLoggingRouteClass(getLogger("FastAPI")))


@app.exception_handler(HTTPException)
def http_exception_handler(req, e):
    return JSONResponse({"code": 500, "error": str(e)}, 500)


@router.post("/top-model")
def requestTopModel(requestBody: RequestFitTopBody):
    # Create and start the BLAST thread
    topModelThread = threading.Thread(target=doFitTop, args=(requestBody,))
    topModelThread.start()

    return {"code": 200, "message": "started fittop thread"}


app.include_router(router)
