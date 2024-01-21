from fastapi import FastAPI
import threading

from dotenv import load_dotenv
load_dotenv()

from modules.fittop.model.model import RequestFitTopBody
from modules.fittop.service.run_top_model import doFitTop
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}   

@app.post("/top-model")
def requestTopModel(requestBody: RequestFitTopBody):
    print('request do top model')
    try:
        # Create and start the FITTOP thread
        topModelThread = threading.Thread(target=doFitTop, args=(requestBody,))
        topModelThread.start()

        return {"message": "Start Top Model Thread"}
    except:
        return {"message": "Fail to start Top Model Thread"}
    
