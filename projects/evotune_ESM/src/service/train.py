import os
import logging
import pkg.common.logger as protenglog

# silence TQDM
if not os.getenv("DEBUG") == "true":
    os.environ["TQDM_DISABLE"] = "1"
    
# silience the evotune logger
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

def trainESM(trainSet, outDomainValSet, config):
    return