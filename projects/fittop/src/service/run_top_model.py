import pickle as pkl
import warnings

warnings.filterwarnings('ignore')

# https://github.com/ElArkk/jax-unirep/blob/e3d756011fd539c803c669495b5c20357c47f661/jax_unirep/utils.py#L56

from pkg.common.db import uploadToBucket
from pkg.common.mq import publishCompletedJobStatusToMQ, publishFailedJobStatusToMQ
from src.logger import fittopLogger as logger
from src.const import FITTOP_SERVICE_NAME, FITTOP_BUCKET_NAME, FITTOP_STAGE_ID
from src.service.top_model_utils import formatData,loadSeqs,doRidgeRegression
from src.model.model import RequestFitTopBody

def doFitTop(requestBody: RequestFitTopBody):
    try:
        data = formatData(requestBody.lab_result.total, requestBody.lab_result.sequences, requestBody.lab_result.scores)
        logger.info(f"job id {requestBody.job_id}: load data ok")
        seqs = loadSeqs(
            seqs_df=data,
            bucket_name=requestBody.artifact.unirep.bucket_name,
            model_path=requestBody.artifact.unirep.path
        )
        logger.info(f"job id {requestBody.job_id}: load seqs ok")
        top_model = doRidgeRegression(
            this_df=seqs,
            train_batch_sizes=requestBody.config.train_batch_sizes,
            n_batch=requestBody.config.n_batch,
            alpha=requestBody.config.alpha
        )
        logger.info(f"job id {requestBody.job_id}: ridge regress ok")
        model_data = pkl.dumps(top_model)
        bucket_name = "ridgecv"
        model_filename = requestBody.job_id + '.pkl'
        upload_result = uploadToBucket(bucket_name, model_filename, model_data)
        logger.info(f"job id {requestBody.job_id}: upload result: {upload_result}")
        publishCompletedJobStatusToMQ(FITTOP_SERVICE_NAME, FITTOP_BUCKET_NAME, FITTOP_STAGE_ID, requestBody.job_id, requestBody.job_id+".pkl")
        logger.info(f"job id {requestBody.job_id} completed successfully")
    except Exception as err:
        logger.error(f"job id {requestBody.job_id}: error do fittop: Unexpected {err=}, {type(err)=}")
        publishFailedJobStatusToMQ(FITTOP_SERVICE_NAME, FITTOP_BUCKET_NAME, FITTOP_STAGE_ID, requestBody.job_id, requestBody.job_id+".pkl", str(err))
