import pickle as pkl
import logging

from src.model.model import RequestEvotuneBody

from src.service.db import getSequencesFromDB, uploadEUnirepToDB
from src.service.train import trainUnirep
from src.service.mq import publishCompletedJobStatusToMQ, publishFailedJobStatusToMQ

def runEvotuneThread(requestBody: RequestEvotuneBody):
    try:
        logging.info(f"job id {requestBody.job_id}: Start Evotune Thread")

        # get train set and validation set from DB
        #   sequence = { 
        #       "train_set": ["sequence1", "sequence2", ...],
        #       "out_domain_val_set": ["sequence1", "sequence2", ...]
        #   }
        logging.debug("Getting sequences from DB...")
        sequences = getSequencesFromDB(requestBody)
        logging.debug("Sequences got!")

        # Evotune
        logging.info(f"job id {requestBody.job_id}: start evotuning")
        _, evotuned_params = trainUnirep(sequences["train_set"], sequences["out_domain_val_set"], requestBody.config)
        logging.info(f"job id {requestBody.job_id}: training done.")

        # Convert evotuned_params to pkl file
        model_weights = pkl.dumps(evotuned_params)

        # Save model_weights (pkl file) to Unirep Object Storage
        logging.debug("Saving evotuned_params...")
        uploadEUnirepToDB(requestBody.job_id+".pkl", model_weights)
        logging.info(f"job id {requestBody.job_id}: evotuned_params saved")

        # Send Success Message to Message Queue
        logging.debug("Sending success message to MQ...")
        publishCompletedJobStatusToMQ(requestBody.job_id, requestBody.job_id+".pkl")
        logging.debug("Success message sent!")

        logging.info(f"job id {requestBody.job_id}: Evotune Thread finished")
    except Exception as err:
        logging.error(f"job id {requestBody.job_id}: error evotune: Unexpected {err=}, {type(err)=}")

        # Send Error Message to Message Queue
        logging.debug("Sending error message to MQ...")
        publishFailedJobStatusToMQ(requestBody.job_id, requestBody.job_id+".pkl", str(err))
        logging.debug("Error message sent!")