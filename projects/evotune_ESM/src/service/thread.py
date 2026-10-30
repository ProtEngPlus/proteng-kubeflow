# # Add the root directory (proteng-kubeflow) to sys.path
# # Add the proteng-kubeflow root directory to sys.path
# pkg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../pkg'))
# if pkg_path not in sys.path:
#     sys.path.insert(0, pkg_path)

# print(sys.path)


import warnings

import pandas as pd
from src.logger import evotuneESMLogger as logger
from src.model.model import RequestEvotuneESMBody
from src.service.db import getSequencesFromDB, uploadESMToDB
from src.service.mq import publishCompletedJobStatusToMQ, publishFailedJobStatusToMQ
from src.service.train import trainESM

from pkg.common.esm import dumpESMModel

warnings.filterwarnings("ignore")


def runEvotuneThread(requestBody: RequestEvotuneESMBody):
    try:
        logger.info(f"job id {requestBody.job_id}: Start Evotune Thread")

        # get train set and validation set from DB
        # sequence = filtered_df from blast
        logger.info("Getting sequences from DB...")

        filtered_df = pd.DataFrame.from_records(
            [query.dict() for query in requestBody.query_result]
        )
        filtered_df.index = range(len(filtered_df))

        data = getSequencesFromDB(requestBody)
        randomState = data["randomState"]

        logger.info("Sequences got!")

        # move from blast
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

        trainSet = trainSet["sequences"].tolist()

        # Evotune
        logger.info(f"job id {requestBody.job_id}: start evotuning")
        model = trainESM(trainSet, requestBody.config)
        logger.info(f"job id {requestBody.job_id}: training done.")

        # Save the fine-tuned model to Unirep Object Storage
        logger.debug("Saving the ESM model...")
        uploadESMToDB(requestBody.job_id + ".pt", dumpESMModel(model))
        logger.info(f"job id {requestBody.job_id}: ESM model saved")

        # Send Success Message to Message Queue
        logger.debug("Sending success message to MQ...")
        publishCompletedJobStatusToMQ(requestBody.job_id, requestBody.job_id + ".pt")
        logger.debug("Success message sent!")

        logger.info(f"job id {requestBody.job_id}: Evotune Thread finished")
    except Exception as err:  # noqa: BLE001 -- reports failure via job-status queue
        logger.error(
            f"job id {requestBody.job_id}: error evotune: Unexpected {err=}, {type(err)=}"
        )

        # Send Error Message to Message Queue
        logger.debug("Sending error message to MQ...")
        publishFailedJobStatusToMQ(
            requestBody.job_id, requestBody.job_id + ".pt", str(err)
        )
        logger.debug("Error message sent!")
