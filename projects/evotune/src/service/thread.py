import pickle as pkl

from src.model.model import RequestEvotuneBody

from pkg.common.logger import evotuneLogger as logger

from src.service.db import getSequencesFromDB, uploadEUnirepToDB
from src.service.train import trainUnirep
from src.service.mq import publishCompletedJobStatusToMQ, publishFailedJobStatusToMQ

import warnings
warnings.filterwarnings('ignore')

def runEvotuneThread(requestBody: RequestEvotuneBody):
    try:
        logger.info(f"job id {requestBody.job_id}: Start Evotune Thread")

        # get train set and validation set from DB
        #   sequence = { 
        #       "train_set": ["sequence1", "sequence2", ...],
        #       "out_domain_val_set": ["sequence1", "sequence2", ...]
        #   }
        logger.debug("Getting sequences from DB...")
        sequences = getSequencesFromDB(requestBody)
        logger.debug("Sequences got!")

        # Evotune
        logger.info(f"job id {requestBody.job_id}: start evotuning")
        _, evotuned_params = trainUnirep(sequences["train_set"], sequences["out_domain_val_set"], requestBody.config)
        logger.info(f"job id {requestBody.job_id}: training done.")

        # Convert evotuned_params to pkl file
        model_weights = pkl.dumps(evotuned_params)

        # Save model_weights (pkl file) to Unirep Object Storage
        logger.debug("Saving evotuned_params...")
        uploadEUnirepToDB(requestBody.job_id+".pkl", model_weights)
        logger.info(f"job id {requestBody.job_id}: evotuned_params saved")

        # Send Success Message to Message Queue
        logger.debug("Sending success message to MQ...")
        publishCompletedJobStatusToMQ(requestBody.job_id, requestBody.job_id+".pkl")
        logger.debug("Success message sent!")

        logger.info(f"job id {requestBody.job_id}: Evotune Thread finished")
    except Exception as err:
        logger.error(f"job id {requestBody.job_id}: error evotune: Unexpected {err=}, {type(err)=}")

        # Send Error Message to Message Queue
        logger.debug("Sending error message to MQ...")
        publishFailedJobStatusToMQ(requestBody.job_id, requestBody.job_id+".pkl", str(err))
        logger.debug("Error message sent!")