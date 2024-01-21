import pickle as pkl

from modules.evotune.model.model import RequestEvotuneBody

from modules.evotune.service.db import getSequencesFromDB, uploadEUnirepToDB
from modules.evotune.service.train import trainUnirep
from modules.evotune.service.mq import publishCompletedJobStatusToMQ, publishFailedJobStatusToMQ

def runEvotuneThread(requestBody: RequestEvotuneBody):
    try:
        print("Start Evotune Thread")

        # get train set and validation set from DB
        #   sequence = { 
        #       "train_set": ["sequence1", "sequence2", ...],
        #       "out_domain_val_set": ["sequence1", "sequence2", ...]
        #   }
        print("Getting sequences from DB...")
        sequences = getSequencesFromDB(requestBody)
        print("Sequences got!")

        # Evotune
        print("Start Evotuning...")
        _, evotuned_params = trainUnirep(sequences["train_set"], sequences["out_domain_val_set"], requestBody.config)
        print("Training done!")

        # Convert evotuned_params to pkl file
        model_weights = pkl.dumps(evotuned_params)

        # Save model_weights (pkl file) to Unirep Object Storage
        print("Saving evotuned_params...")
        uploadEUnirepToDB(requestBody.job_id+".pkl", model_weights)
        print("evotuned_params saved!")

        # Send Success Message to Message Queue
        print("Sending success message to MQ...")
        publishCompletedJobStatusToMQ(requestBody.job_id, requestBody.job_id+".pkl")
        print("Success message sent!")

        print("Evotune Thread finished")
    except Exception as err:
        # Send Error Message to Message Queue
        print("Sending error message to MQ...")
        publishFailedJobStatusToMQ(requestBody.job_id, requestBody.job_id+".pkl", str(err))
        print("Error message sent!")

        print(f"Unexpected {err=}, {type(err)=}")