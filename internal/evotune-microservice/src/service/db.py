import json

from common.db import downloadFromBucket, uploadToBucket
from src.model.model import RequestEvotuneBody
from src.const import EVOTUNE_BUCKET_NAME

def getSequencesFromDB(requestBody: RequestEvotuneBody):
    # Download sequence data from Blast Object Storage
    # sequences = { 
    #   "train_set": ["sequence1", "sequence2", ...],
    #   "out_domain_val_set": ["sequence1", "sequence2", ...]
    # }
    sequences = downloadFromBucket(requestBody.artifact.blast.bucket_name, requestBody.artifact.blast.path)
    sequences = json.loads(sequences)
    return sequences

def uploadEUnirepToDB(filePath, model_weights):
    # Save evotuned_params to Unirep Object Storage
    uploadToBucket(EVOTUNE_BUCKET_NAME, filePath, model_weights)
    return True