import json

from src.const import EVOTUNE_BUCKET_NAME
from src.model.model import RequestEvotuneESMBody

from pkg.common.db import downloadFromBucket, uploadToBucket


def getSequencesFromDB(requestBody: RequestEvotuneESMBody):
    # Download sequence data from Blast Object Storage
    # sequences = {
    #   "query_results": ["sequence1", "sequence2", ...],
    #   "randomState": int
    # }
    sequences = downloadFromBucket(
        requestBody.artifact.blast.bucket_name, requestBody.artifact.blast.path
    )
    sequences = sequences.decode("utf-8")
    data = json.loads(sequences)
    return data


def uploadESMToDB(filePath, model_weights):
    # Save evotuned_params to Unirep Object Storage
    uploadToBucket(EVOTUNE_BUCKET_NAME, filePath, model_weights)
    return True
