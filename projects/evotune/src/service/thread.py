import pickle as pkl
import warnings

import pandas as pd
from src.logger import evotuneLogger as logger
from src.model.model import RequestEvotuneBody
from src.service.db import getSequencesFromDB, uploadEUnirepToDB
from src.service.mq import publishCompletedJobStatusToMQ, publishFailedJobStatusToMQ
from src.service.train import trainUnirep

warnings.filterwarnings("ignore")


def runEvotuneThread(requestBody: RequestEvotuneBody):
    try:
        logger.info(f"job id {requestBody.job_id}: Start Evotune Thread")

        # get train set and validation set from DB
        # sequence = filtered_df from protein query
        logger.info("Getting sequences from DB...")

        filtered_df = pd.DataFrame.from_records(
            [query.dict() for query in requestBody.query_result]
        )
        filtered_df.index = range(len(filtered_df))

        data = getSequencesFromDB(requestBody)
        randomState = data["randomState"]

        logger.info("Sequences got!")

        # move from protein query
        # frac=0.1 rounds down to 0 rows whenever there are fewer than ~10
        # sequences, leaving jax_unirep with an empty validation set - always
        # take at least 1 sequence for the held-out set.
        valSetSize = max(1, round(len(filtered_df) * 0.1))
        if filtered_df["score"].sum() == 0:
            logger.warning(
                "The 'score' column has all zero values. Falling back to simple random sampling."
            )
            # Use simple random sampling without weights
            outDomainValSet = filtered_df.sample(n=valSetSize, random_state=randomState)
            trainSet = filtered_df.drop(outDomainValSet.index)
        else:
            # Perform weighted sampling
            outDomainValSet = filtered_df.sample(
                n=valSetSize, weights="score", random_state=randomState
            )
            trainSet = filtered_df.drop(outDomainValSet.index)

        outDomainValSet = outDomainValSet["sequences"].tolist()
        trainSet = trainSet["sequences"].tolist()

        # Create a dictionary to store the results
        sequences = {
            "train_set": trainSet,
            "out_domain_val_set": outDomainValSet,
        }

        # Evotune
        logger.info(f"job id {requestBody.job_id}: start evotuning")
        _, evotuned_params = trainUnirep(
            sequences["train_set"], sequences["out_domain_val_set"], requestBody.config
        )
        logger.info(f"job id {requestBody.job_id}: training done.")

        # Convert evotuned_params to pkl file
        model_weights = pkl.dumps(evotuned_params)

        # Save model_weights (pkl file) to Unirep Object Storage
        logger.debug("Saving evotuned_params...")
        uploadEUnirepToDB(requestBody.job_id + ".pkl", model_weights)
        logger.info(f"job id {requestBody.job_id}: evotuned_params saved")

        # Send Success Message to Message Queue
        logger.debug("Sending success message to MQ...")
        publishCompletedJobStatusToMQ(requestBody.job_id, requestBody.job_id + ".pkl")
        logger.debug("Success message sent!")

        logger.info(f"job id {requestBody.job_id}: Evotune Thread finished")
    except Exception as err:  # noqa: BLE001 -- reports failure via job-status queue
        logger.error(
            f"job id {requestBody.job_id}: error evotune: Unexpected {err=}, {type(err)=}"
        )

        # Send Error Message to Message Queue
        logger.debug("Sending error message to MQ...")
        publishFailedJobStatusToMQ(
            requestBody.job_id, requestBody.job_id + ".pkl", str(err)
        )
        logger.debug("Error message sent!")
