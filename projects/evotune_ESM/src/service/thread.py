import sys
import os


# # Add the root directory (proteng-kubeflow) to sys.path
# # Add the proteng-kubeflow root directory to sys.path
# pkg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../pkg'))
# if pkg_path not in sys.path:
#     sys.path.insert(0, pkg_path)

# print(sys.path)


import pickle as pkl
import pandas as pd
import json
from json import loads, dumps
from src.model.model import RequestEvotuneESMBody

from src.logger import evotuneESMLogger as logger

from src.service.db import getSequencesFromDB, uploadESMToDB
from src.service.train import trainESM
from src.service.mq import publishCompletedJobStatusToMQ, publishFailedJobStatusToMQ

import warnings
warnings.filterwarnings('ignore')

def runEvotuneThread(requestBody: RequestEvotuneESMBody):
    try:
        logger.info(f"job id {requestBody.job_id}: Start Evotune Thread")

        # get train set and validation set from DB
        # sequence = filtered_df from blast
        logger.info("Getting sequences from DB...")
    
        filtered_df = pd.DataFrame.from_records([query.dict() for query in requestBody.query_result])
        filtered_df.index = range(len(filtered_df))
        
        data = getSequencesFromDB(requestBody)
        randomState = data['randomState']
        
        logger.info("Sequences got!")
        
        # move from blast
        if filtered_df['score'].sum() == 0:
            logger.warning("The 'score' column has all zero values. Falling back to simple random sampling.")
            # Use simple random sampling without weights
            outDomainValSet = filtered_df.sample(frac=0.1, random_state=randomState)
            trainSet = filtered_df.drop(outDomainValSet.index)
        else:
            # Perform weighted sampling
            outDomainValSet = filtered_df.sample(frac=0.1, weights="score", random_state=randomState)
            trainSet = filtered_df.drop(outDomainValSet.index)

        outDomainValSet = outDomainValSet["sequences"].tolist()[:2]
        trainSet = trainSet["sequences"].tolist()[:2]

        # Create a dictionary to store the results
        sequences = {
            "train_set": trainSet,
            "out_domain_val_set": outDomainValSet,
        }

        # Evotune
        logger.info(f"job id {requestBody.job_id}: start evotuning")
        df = trainESM(sequences["train_set"], sequences["out_domain_val_set"], requestBody.config)
        esm_np = df.to_numpy()
        logger.info(f"job id {requestBody.job_id}: training done.")

        # Convert evotuned_params to pkl file
        model_weights = pkl.dumps(esm_np)

        # Save model_weights (pkl file) to Unirep Object Storage
        logger.debug("Saving esm_np...")
        uploadESMToDB(requestBody.job_id+".pkl", model_weights)
        logger.info(f"job id {requestBody.job_id}: esm_np saved")

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