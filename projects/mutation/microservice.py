import threading
import sys
sys.path.append("../")
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI

from src.service.thread import runMutationThread
from src.model.model import RequestMutationBody

app = FastAPI()

@app.post("/mutation")
def requestEvotune(requestBody: RequestMutationBody):
    print("----------------------------------------------------------")
    print("requesting mutation service...")
    print(requestBody)
    try:
        # Create and start the MUTATION thread
        mutationThread = threading.Thread(target=runMutationThread, args=(requestBody,))
        mutationThread.start()
        
        return {"run_mutation_thread":"success"}
    except:
        return {"run_mutation_thread":"fail"}