import sys
import os
# print(sys.path)

# Add the root directory (proteng-kubeflow) to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.append(project_root)

# sys.path.append("../../../..")


import logging
import pkg.common.logger as protenglog
import pandas as pd
import numpy as np

# silence TQDM
if not os.getenv("DEBUG") == "true":
    os.environ["TQDM_DISABLE"] = "1"
    
# silence optuna logger
import optuna.logging as optunalog
def _silent_optuna_get_logger(__name__):
    optunalogger = protenglog.getLogger(__name__)
    optunalogger.setLevel(logging.ERROR)
    optunalogger.propagate = False

optunalog.get_logger = _silent_optuna_get_logger

import torch
import pandas as pd
from Bio import SeqIO
from transformers import AutoTokenizer
from datasets import Dataset
from transformers import AutoModelForMaskedLM
from transformers import DataCollatorForLanguageModeling
from transformers import TrainingArguments, Trainer
import esm
import tempfile
from torch import nn
import re

def get_latest_checkpoint_by_number(checkpoint_dir):
    checkpoint_dirs = [f for f in os.scandir(checkpoint_dir) if f.is_dir() and f.name.startswith("checkpoint")]
    def extract_number(f):  # Extract the number after 'checkpoint-'
        match = re.search(r"checkpoint-(\d+)", f.name)
        return int(match.group(1)) if match else -1

    latest_checkpoint = max(checkpoint_dirs, key=extract_number)
    return latest_checkpoint.path


# Wrapper for last-layer stripping
class EsmLMHeadWithoutDecoder(nn.Module):
    def __init__(self, lm_head):
        super().__init__()
        self.dense = lm_head.dense
        self.layer_norm = lm_head.layer_norm

    def forward(self, hidden_states):
        hidden_states = self.dense(hidden_states)
        hidden_states = self.layer_norm(hidden_states)
        return hidden_states

class EsmForMaskedLMWithoutLastLayer(nn.Module):
    def __init__(self, esm_model):
        super().__init__()
        self.esm = esm_model.esm
        self.lm_head = EsmLMHeadWithoutDecoder(esm_model.lm_head)

    def forward(self, input_ids):
        output = self.esm(input_ids)
        hidden_states = output.last_hidden_state
        lm_logits = self.lm_head(hidden_states)
        return lm_logits


def trainESM(trainSet, outDomainValSet, config):
    torch.mps.empty_cache()
    if torch.backends.mps.is_available():
        mps_device = torch.device("mps")
        x = torch.ones(1, device=mps_device)
        print (x)
    else:
        print ("MPS device not found.")
        
    model_checkpoint = "facebook/esm2_t33_650M_UR50D"
    
    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
    
    train_tokenized = tokenizer(trainSet)
    test_tokenized = tokenizer(outDomainValSet)

    train_dataset = Dataset.from_dict(train_tokenized)
    test_dataset = Dataset.from_dict(test_tokenized)

    train_labels = [0 for protein in trainSet]
    train_dataset = train_dataset.add_column("labels", train_labels)

    test_labels = [0 for protein in outDomainValSet]
    test_dataset = test_dataset.add_column("labels", test_labels)

    tokenizer.pad_token = tokenizer.eos_token
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm_probability=0.15)

    model = AutoModelForMaskedLM.from_pretrained(model_checkpoint)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        training_args = TrainingArguments(
            output_dir="eESM-BIOTEC-TreS",
            # evaluation_strategy="epoch",
            learning_rate=config['learning_rate_config'],
            num_train_epochs=config['n_epochs_config'],
            weight_decay=config['weight_decay'],
            push_to_hub=False,
        )

        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=test_dataset,
            data_collator=data_collator,
        )

        trainer.train()
        
        checkpoint_path = get_latest_checkpoint_by_number(temp_dir)

        model = AutoModelForMaskedLM.from_pretrained(checkpoint_path)
        model = EsmForMaskedLMWithoutLastLayer(model)
    
    _, alphabet = esm.pretrained.esm2_t33_650M_UR50D()

    # Load ESM-2 model
    batch_converter = alphabet.get_batch_converter()
    model.eval()  # disables dropout for deterministic results
    
    # Prepare data
    data = [(f"seq{i+1}", seq) for i, seq in enumerate(trainSet + outDomainValSet)]
    batch_labels, batch_strs, batch_tokens = batch_converter(data)
    batch_lens = (batch_tokens != alphabet.padding_idx).sum(1)
    
    # Create a DataFrame to store the sequence representations
    df = pd.DataFrame()
    
    # Extract per-residue representations for each sequence
    with torch.no_grad():
        for i in range(len(batch_tokens)):
            tokens = batch_tokens[i]

            # Convert tokens to a tensor
            input_tokens = tokens.clone().detach()

            results = model(input_tokens.unsqueeze(0))
            #token_representations = results["representations"][33]

            flattened_representation = results.view(-1)
            # print(flattened_representation.shape)

            flattened_representation = results.view(-1, results.size(-1))  # Reshape to (num_tokens, embedding_size)
            # print(flattened_representation.shape)
            flattened_representation = flattened_representation.mean(dim=0)  # Compute mean along the first dimension
            print(flattened_representation.shape)

            # Convert the list of tensors to a DataFrame row by row
            if i == 0:
                df = pd.DataFrame(flattened_representation.numpy()).T
            else:
                df = pd.concat([df, pd.DataFrame(flattened_representation.numpy()).T], ignore_index=True)

            print(i)

    print(df, flush=True)

    df.to_feather(directory_path + 'BIOTEC-eESM-avg.feather')
    return df
    
    