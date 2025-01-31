import json
from io import StringIO
from json import loads, dumps
from pkg.common.db import downloadFromBucket, uploadToBucket
from src.model.model import RequestEvotuneBody
from src.const import EVOTUNE_BUCKET_NAME

def getSequencesFromDB(requestBody: RequestEvotuneBody):
    # Download sequence data from Blast Object Storage
    # sequences = { 
    #   "query_results": ["sequence1", "sequence2", ...],
    #   "randomState": int
    # }
    sequences = downloadFromBucket(requestBody.artifact.blast.bucket_name, requestBody.artifact.blast.path)
    sequences = sequences.decode('utf-8')
    data = json.loads(sequences)
    return data

def uploadEUnirepToDB(filePath, model_weights):
    # Save evotuned_params to Unirep Object Storage
    uploadToBucket(EVOTUNE_BUCKET_NAME, filePath, model_weights)
    return True