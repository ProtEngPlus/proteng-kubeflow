import pickle as pkl

from jax.random import PRNGKey
from jax_unirep import evotune
from jax_unirep.evotuning_models import mlstm64

from src.model.model import RequestEvotuneBody

from src.service.db import getSequencesFromDB, uploadEUnirepToDB
from src.service.train import trainUnirep
from common.db import uploadToBucket

def runEvotuneThread(requestBody: RequestEvotuneBody):
    try:
        print("Start Evotune Thread")

        # get train set and validation set from DB
        #   sequence = { 
        #       "train_set": ["sequence1", "sequence2", ...],
        #       "out_domain_val_set": ["sequence1", "sequence2", ...]
        #   }
        sequences = getSequencesFromDB(requestBody)

        # Evotune
        print("Start Evotuning...")
        _, evotuned_params = trainUnirep(sequences["train_set"], sequences["out_domain_val_set"], requestBody.config)
        print("Training done!")

        # Convert evotuned_params to pkl file
        model_weights = pkl.dumps(evotuned_params)

        # Save model_weights (pkl file) to Unirep Object Storage
        print("Saving evotuned_params...")
        uploadEUnirepToDB(requestBody.job_id, model_weights)
        print("evotuned_params saved!")

        # TODO: Send Success Message to Message Queue

        print("Evotune Thread finished")
    except Exception as err:
        # TODO: Send Error Message to Message Queue

        print(f"Unexpected {err=}, {type(err)=}")