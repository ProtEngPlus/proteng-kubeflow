from src.model.model import RequestMutationBody
from src.service.db import getParamsFromDB, getModelFromDB
from src.service.directed_evo import runDirectedEvoTrajectories
from src.service.mq import publishCompletedJobStatusToMQ, publishFailedJobStatusToMQ
from src.service.utils import convertTwoArraysToDict

def runMutationThread(requestBody: RequestMutationBody):
    try:
        print("Start Mutation Thread")
        # get e unirep params from DB
        print("Getting e unirep params from DB...")
        params = getParamsFromDB(requestBody.artifact.unirep.bucket_name, requestBody.artifact.unirep.path)
        print("Params got!")

        # get fit top model from DB
        print("Getting fit top model from DB...")
        model = getModelFromDB(requestBody.artifact.ridgecv.bucket_name, requestBody.artifact.ridgecv.path)
        print("Model got!")

        # run directed evolution
        print("Running directed evolution...")
        s_records, fitness_records = runDirectedEvoTrajectories(requestBody.input, model, requestBody.config.temperature, requestBody.config.num_iterations, requestBody.config.num_trajectories, params)
        print("Directed evolution done!")

        # Send Success Message to Message Queue
        print("Sending success message to MQ...")
        publishCompletedJobStatusToMQ(requestBody.job_id, requestBody.mutation_id, convertTwoArraysToDict(s_records[:, -1], fitness_records[:, -1, 0]))
        print("Success message sent!")

        print("Mutation Thread finished")
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")

        # Send Error Message to Message Queue
        print("Sending error message to MQ...")
        publishFailedJobStatusToMQ(requestBody.job_id, requestBody.mutation_id, "", str(err))
        print("Error message sent!")
