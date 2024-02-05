import threading
import sys
sys.path.append("../../")
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from src.service.thread import runMutationThread
from src.model.model import RequestMutationBody

from pkg.common.logger import getLogger

logger = getLogger("mutation_service")

app = FastAPI()

@app.exception_handler(HTTPException)
def http_exception_handler(req, e):
    return JSONResponse({"code": 500, "error": str(e)}, 500)

@app.post("/mutation")
def requestEvotune(requestBody: RequestMutationBody):
    logger.debug("----------------------------------------------------------")
    logger.debug("requesting mutation service...")
    logger.debug(requestBody)
    try:
        # Create and start the MUTATION thread
        mutationThread = threading.Thread(target=runMutationThread, args=(requestBody,))
        mutationThread.start()
        
        return {"code": 200, "message": "started mutation thread"}
    except Exception as e:
        raise e