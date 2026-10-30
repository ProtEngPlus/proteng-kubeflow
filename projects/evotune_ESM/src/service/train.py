import logging
import os

import pkg.common.logger as protenglog

# silence TQDM
if os.getenv("DEBUG") != "true":
    os.environ["TQDM_DISABLE"] = "1"

# silence optuna logger
import optuna.logging as optunalog


def _silent_optuna_get_logger(__name__):
    optunalogger = protenglog.getLogger(__name__)
    optunalogger.setLevel(logging.ERROR)
    optunalogger.propagate = False


optunalog.get_logger = _silent_optuna_get_logger

import tempfile

from datasets import Dataset
from transformers import (
    AutoModelForMaskedLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

from pkg.common.esm import ESM_MODEL_NAME


def trainESM(trainSet, config):
    # fine-tune ESM-2 with masked language modeling on the query result sequences
    tokenizer = AutoTokenizer.from_pretrained(ESM_MODEL_NAME)
    train_dataset = Dataset.from_dict(tokenizer(trainSet, truncation=True))
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, mlm_probability=0.15
    )

    model = AutoModelForMaskedLM.from_pretrained(ESM_MODEL_NAME)

    with tempfile.TemporaryDirectory() as temp_dir:
        training_args = TrainingArguments(
            output_dir=temp_dir,
            save_strategy="no",
            learning_rate=config.learning_rate_config,
            num_train_epochs=config.n_epochs_config,
            weight_decay=config.weight_decay,
            report_to="none",
            push_to_hub=False,
        )
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=data_collator,
        )
        trainer.train()

    return trainer.model
