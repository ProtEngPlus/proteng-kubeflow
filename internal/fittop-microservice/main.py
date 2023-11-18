from fastapi import FastAPI
from pydantic import BaseModel
from Bio.Blast import NCBIWWW
import re
import pandas as pd
from typing import List, Optional
import threading

from dotenv import load_dotenv
load_dotenv()

from src.model.model import requestTopModelBody
from src.service.run_top_model import do_top_model
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}   

@app.post("/top-model")
def request_top_model():
# def request_top_model(requestBody: requestTopModelBody):
    # print(requestBody)
    print('request do top model')
    try:
        # Create and start the BLAST thread
        topModelThread = threading.Thread(target=do_top_model, args=())
        topModelThread.start()

        return {"message": "Start Top Model Thread"}
    except:
        return {"message": "Fail to start Top Model Thread"}
    # do_top_model(PARAMS=[None])
    # do_top_model(PARAMS=['one_hot',None,'model.pkl'])

request_top_model()
