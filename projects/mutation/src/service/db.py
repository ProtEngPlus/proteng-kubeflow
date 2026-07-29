import pickle as pkl
from pkg.common.db import downloadFromBucket


def getParamsFromDB(bucket_name, model_path):
    return pkl.loads(downloadFromBucket(bucket_name, model_path))[1]


def getModelFromDB(bucket_name, model_path):
    return pkl.loads(downloadFromBucket(bucket_name, model_path))
