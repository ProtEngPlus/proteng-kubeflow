import logging
from src.model.model import RequestMutationBody
from src.service.db import getParamsFromDB, getModelFromDB
from src.service.directed_evo import runDirectedEvoTrajectories
from src.service.mq import publishCompletedJobStatusToMQ, publishFailedJobStatusToMQ
from src.service.utils import convertTwoArraysToDict

def runMutationThread(requestBody: RequestMutationBody):
    try:
        logging.info(f"job id {requestBody.job_id}: Start Mutation Thread")
        # get e unirep params from DB
        logging.debug("Getting e unirep params from DB...")
        params = getParamsFromDB(requestBody.artifact.unirep.bucket_name, requestBody.artifact.unirep.path)
        logging.debug("Params got!")

        # get fit top model from DB
        logging.debug("Getting fit top model from DB...")
        model = getModelFromDB(requestBody.artifact.ridgecv.bucket_name, requestBody.artifact.ridgecv.path)
        logging.debug("Model got!")

        # run directed evolution
        logging.info(f"job id {requestBody.job_id}: running directed evolution...")
        s_records, fitness_records = runDirectedEvoTrajectories(requestBody.input, model, requestBody.config.temperature, requestBody.config.num_iterations, requestBody.config.num_trajectories, params)
        logging.info(f"job id {requestBody.job_id}: directed evolution done.")

        # Send Success Message to Message Queue
        logging.debug("Sending success message to MQ...")
        publishCompletedJobStatusToMQ(requestBody.job_id, requestBody.mutation_id, convertTwoArraysToDict(s_records[:, -1], fitness_records[:, -1, 0]))
        logging.debug("Success message sent!")

        logging.info(f"job id {requestBody.job_id}: Mutation Thread finished")
    except Exception as err:
        logging.error(f"job id {requestBody.job_id}: error mutation: Unexpected {err=}, {type(err)=}")

        # Send Error Message to Message Queue
        logging.debug("Sending error message to MQ...")
        publishFailedJobStatusToMQ(requestBody.job_id, requestBody.mutation_id, "", str(err))
        logging.debug("Error message sent!")
