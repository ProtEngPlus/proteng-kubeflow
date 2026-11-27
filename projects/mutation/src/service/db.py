import pickle as pkl

from pkg.common.db import downloadFromBucket
from pkg.common.esm import loadESMModel


def getParamsFromDB(bucket_name, model_path, representation_type="unirep"):
    data = downloadFromBucket(bucket_name, model_path)
    if representation_type.lower() == "esm":
        return loadESMModel(data)
    return pkl.loads(data)[1]


def getModelFromDB(bucket_name, model_path):
    return pkl.loads(downloadFromBucket(bucket_name, model_path))
