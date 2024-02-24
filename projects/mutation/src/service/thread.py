from src.model.model import RequestMutationBody
from src.service.db import getParamsFromDB, getModelFromDB
from src.service.directed_evo import runDirectedEvoTrajectories
from src.service.mq import publishCompletedJobStatusToMQ, publishFailedJobStatusToMQ
from src.service.utils import convertTwoArraysToDict
from src.logger import mutationLogger as logger

def runMutationThread(requestBody: RequestMutationBody):
    try:
        logger.info(f"job id {requestBody.job_id}: Start Mutation Thread")
        # get e unirep params from DB
        logger.debug("Getting e unirep params from DB...")
        params = getParamsFromDB(requestBody.artifact.unirep.bucket_name, requestBody.artifact.unirep.path)
        logger.debug("Params got!")

        # get fit top model from DB
        logger.debug("Getting fit top model from DB...")
        model = getModelFromDB(requestBody.artifact.ridgecv.bucket_name, requestBody.artifact.ridgecv.path)
        logger.debug("Model got!")

        # run directed evolution
        logger.info(f"job id {requestBody.job_id}: running directed evolution...")
        s_records, fitness_records = runDirectedEvoTrajectories(requestBody.input, model, requestBody.config.temperature, requestBody.config.num_iterations, requestBody.config.num_trajectories, params)
        logger.info(f"job id {requestBody.job_id}: directed evolution done.")

        # Send Success Message to Message Queue
        logger.debug("Sending success message to MQ...")
        logger.info(f"s records {s_records.shape} fitness_records {fitness_records.shape}")
        publishCompletedJobStatusToMQ(requestBody.job_id, requestBody.mutation_id, convertTwoArraysToDict(s_records[:, -1], fitness_records[:, -1, 0]))
        logger.debug("Success message sent!")

        logger.info(f"job id {requestBody.job_id}: Mutation Thread finished")
    except Exception as err:
        logger.error(f"job id {requestBody.job_id}: error mutation: Unexpected {err=}, {type(err)=}")

        # Send Error Message to Message Queue
        logger.debug("Sending error message to MQ...")
        publishFailedJobStatusToMQ(requestBody.job_id, requestBody.mutation_id, "", str(err))
        logger.debug("Error message sent!")
