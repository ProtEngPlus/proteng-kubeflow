import pickle as pkl

from jax.random import PRNGKey
from jax_unirep import evotune
from jax_unirep.evotuning_models import mlstm64
from jax_unirep.utils import dump_params

from src.model.model import RequestEvotuneBody

from src.service.db import getSequencesFromDB
from common.db import createBucket, uploadToBucket, downloadFromBucket

def runEvotuneThread(requestBody: RequestEvotuneBody):
    try:
        print("Start Evotune Thread")

        # get train set and validation set
        # requestBody.dataset_url
        sequences = getSequencesFromDB("sequence", requestBody.job_id, requestBody.sequence_path)

        init_fun, apply_fun = mlstm64()
        # The input_shape is always going to be (-1, 26),
        # because that is the number of unique AA, one-hot encoded.
        _, inital_params = init_fun(PRNGKey(42), input_shape=(-1, 26))

        # 1. Evotuning with Optuna
        # n_epochs_config = {"low": 1, "high": 1}
        # lr_config = {"low": 1e-5, "high": 1e-3}
        study, evotuned_params = evotune(
            sequences=sequences["train_set"],
            model_func=apply_fun,
            params=inital_params,
            out_dom_seqs=sequences["out_domain_val_set"],
            n_trials=requestBody.evotune_params.n_trials,
            n_splits=requestBody.evotune_params.n_splits,
            n_epochs_config=requestBody.evotune_params.n_epochs_config,
            learning_rate_config=requestBody.evotune_params.learning_rate_config,
        )
        print("Training done!")

        # Save evotuned_params
        model_weights = pkl.dumps(evotuned_params)
        print("Saving evotuned_params...")
        uploadToBucket("unirep", requestBody.job_id, requestBody.eUnirep_path+".pkl", model_weights)
        print("evotuned_params saved!")

        print("Evotune Thread finished")
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")