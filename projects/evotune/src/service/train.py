import os
# silence TQDM
if not os.getenv("DEBUG") == "true":
    os.environ["TQDM_DISABLE"] = "1"

from jax.random import PRNGKey
from jax_unirep import evotune
from jax_unirep.evotuning_models import mlstm64
import logging

# silience the evotune logger
evotuneLogger = logging.getLogger("evotuning")
if evotuneLogger.hasHandlers():
    evotuneLogger.handlers.clear()
evotuneLogger.setLevel(logging.CRITICAL)


def trainUnirep(trainSet, outDomainValSet, config):
    init_fun, apply_fun = mlstm64()
    # The input_shape is always going to be (-1, 26),
    # because that is the number of unique AA, one-hot encoded.
    _, initial_params = init_fun(PRNGKey(42), input_shape=(-1, 26))

    # Evotuning With Optuna
    study, evotuned_params = evotune(
        sequences=trainSet,
        model_func=apply_fun,
        params=initial_params,
        out_dom_seqs=outDomainValSet,
        n_trials=config.n_trials,
        n_splits=config.n_splits,
        n_epochs_config=config.n_epochs_config,
        learning_rate_config=config.learning_rate_config,
    )
    return study, evotuned_params