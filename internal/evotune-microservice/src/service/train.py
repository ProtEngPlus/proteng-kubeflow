from jax.random import PRNGKey

from jax_unirep import evotune
from jax_unirep.evotuning_models import mlstm64
from jax_unirep.utils import dump_params

def evotune_thread():
    # get train set 
    sequences = ["HASTA", "VISTA", "ALAVA", "LIMED", "HAST", "HAS", "HASVASTA"] * 5

    # get validation set
    holdout_sequences = [
        "HASTA",
        "VISTA",
        "ALAVA",
        "LIMED",
        "HAST",
        "HASVALTA",
    ] * 5

    init_fun, apply_fun = mlstm64()
    # The input_shape is always going to be (-1, 26),
    # because that is the number of unique AA, one-hot encoded.
    _, inital_params = init_fun(PRNGKey(42), input_shape=(-1, 26))

    # 1. Evotuning with Optuna
    # n_epochs_config = {"low": 1, "high": 1}
    # lr_config = {"low": 1e-5, "high": 1e-3}
    study, evotuned_params = evotune(
        sequences=sequences,
        model_func=apply_fun,
        params=inital_params,
        out_dom_seqs=holdout_sequences,
        n_trials=requestBody.evotune_params.n_trials,
        n_splits=requestBody.evotune_params.n_splits,
        n_epochs_config=requestBody.evotune_params.n_epochs_config,
        learning_rate_config=requestBody.evotune_params.learning_rate_config,
    )