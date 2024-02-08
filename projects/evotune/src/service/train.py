import os
import logging
import pkg.common.logger as protenglog

# silence TQDM
if not os.getenv("DEBUG") == "true":
    os.environ["TQDM_DISABLE"] = "1"

# silience the evotune logger
import jax_unirep.evotuning as evotunelib
def _silent_evotuning_log():
    if evotunelib.logger.hasHandlers():
        evotunelib.logger.handlers.clear()
    evotunelib.logger.setLevel(logging.ERROR)
    evotunelib.logger.propagate = False

evotunelib.setup_evotuning_log = _silent_evotuning_log

# silence optuna logger
import optuna.logging as optunalog
def _silent_optuna_get_logger(__name__):
    optunalogger = protenglog.getLogger(__name__)
    optunalogger.setLevel(logging.ERROR)
    optunalogger.propagate = False

optunalog.get_logger = _silent_optuna_get_logger

from jax.random import PRNGKey
from jax_unirep import evotune
from jax_unirep.evotuning_models import mlstm64

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