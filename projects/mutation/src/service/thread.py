from src.logger import mutationLogger as logger
from src.model.model import RequestMutationBody
from src.service.db import getModelFromDB, getParamsFromDB
from src.service.directed_evo import runDirectedEvoTrajectories
from src.service.mq import publishCompletedJobStatusToMQ, publishFailedJobStatusToMQ
from src.service.mutation_space import getAminoAcids
from src.service.utils import convertTwoArraysToDict


def runMutationThread(requestBody: RequestMutationBody):
    try:
        logger.info(f"job id {requestBody.job_id}: Start Mutation Thread")

        evotune_model_type = requestBody.meta[1]

        # get e unirep params from DB
        logger.debug("Getting e unirep params from DB...")
        params = getParamsFromDB(
            requestBody.artifact[requestBody.meta[1]].bucket_name,
            requestBody.artifact[requestBody.meta[1]].path,
        )
        logger.debug("Params got!")

        # get fit top model from DB
        logger.debug("Getting fit top model from DB...")
        model = getModelFromDB(
            requestBody.artifact[requestBody.meta[2]].bucket_name,
            requestBody.artifact[requestBody.meta[2]].path,
        )
        logger.debug("Model got!")

        # run directed evolution
        logger.info(f"job id {requestBody.job_id}: running directed evolution...")
        config = requestBody.config
        s_records, fitness_records = runDirectedEvoTrajectories(
            requestBody.input,
            model,
            config.temperature,
            config.num_iterations,
            config.num_trajectories,
            config.mutate_regions,
            config.num_mutations_low,
            config.num_mutations_high,
            getAminoAcids(config.amino_acid_set),
            params,
            evotune_model_type,
        )
        logger.info(f"job id {requestBody.job_id}: directed evolution done.")

        # Send Success Message to Message Queue
        logger.debug("Sending success message to MQ...")
        logger.info(
            f"s records {len(s_records)} fitness_records {len(fitness_records)}"
        )
        publishCompletedJobStatusToMQ(
            requestBody.job_id,
            requestBody.mutation_id,
            convertTwoArraysToDict(s_records, fitness_records),
        )
        logger.debug("Success message sent!")

        logger.info(f"job id {requestBody.job_id}: Mutation Thread finished")
    except Exception as err:  # noqa: BLE001 -- reports failure via job-status queue
        logger.error(
            f"job id {requestBody.job_id}: error mutation: Unexpected {err=}, {type(err)=}"
        )

        # Send Error Message to Message Queue
        logger.debug("Sending error message to MQ...")
        publishFailedJobStatusToMQ(
            requestBody.job_id, requestBody.mutation_id, "", str(err)
        )
        logger.debug("Error message sent!")
