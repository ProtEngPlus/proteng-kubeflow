import pickle as pkl
import warnings

warnings.filterwarnings('ignore')

# https://github.com/ElArkk/jax-unirep/blob/e3d756011fd539c803c669495b5c20357c47f661/jax_unirep/utils.py#L56

from common.db import uploadToBucket
from common.mq import publishCompletedJobStatusToMQ, publishFailedJobStatusToMQ
from src.const import FITTOP_SERVICE_NAME, FITTOP_BUCKET_NAME, FITTOP_STAGE_ID
from src.service.top_model_utils import formatData,loadSeqs,doRidgeRegression
from src.model.model import RequestFitTopBody

def doFitTop(requestBody: RequestFitTopBody):
    try:
        data = formatData(requestBody.lab_result.total, requestBody.lab_result.sequences, requestBody.lab_result.scores)
        print('load data ok')
        seqs = loadSeqs(
            seqs_df=data,
            bucket_name=requestBody.artifact.unirep.bucket_name,
            model_path=requestBody.artifact.unirep.path
        )
        print('load seqs ok')
        top_model = doRidgeRegression(
            this_df=seqs,
            train_batch_sizes=requestBody.config.train_batch_sizes,
            n_batch=requestBody.config.n_batch,
            alpha=requestBody.config.alpha
        )
        print('ridge regress ok')
        model_data = pkl.dumps(top_model)
        bucket_name = "ridgecv"
        model_filename = requestBody.job_id + '.pkl'
        upload_result = uploadToBucket(bucket_name, model_filename, model_data)
        print(upload_result)
        publishCompletedJobStatusToMQ(FITTOP_SERVICE_NAME, FITTOP_BUCKET_NAME, FITTOP_STAGE_ID, requestBody.job_id, requestBody.job_id+".pkl")
        print("message ok pushed")
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        publishFailedJobStatusToMQ(FITTOP_SERVICE_NAME, FITTOP_BUCKET_NAME, FITTOP_STAGE_ID, requestBody.job_id, requestBody.job_id+".pkl", str(err))
        print("message fail pushed")
