# torch and transformers are imported inside the functions, so UniRep never needs them
import io

import numpy as np

ESM_MODEL_NAME = "facebook/esm2_t30_150M_UR50D"


def dumpESMModel(model):
    # only the encoder of the fine-tuned EsmForMaskedLM is needed, stored as fp16
    import torch

    state = {key: value.half().cpu() for key, value in model.esm.state_dict().items()}
    buffer = io.BytesIO()
    torch.save({"model_name": ESM_MODEL_NAME, "state_dict": state}, buffer)
    return buffer.getvalue()


def loadESMModel(data):
    import torch
    from transformers import AutoConfig, AutoTokenizer, EsmModel

    saved = torch.load(io.BytesIO(data), map_location="cpu")
    config = AutoConfig.from_pretrained(saved["model_name"])
    model = EsmModel(config, add_pooling_layer=False)
    model.load_state_dict(
        {key: value.float() for key, value in saved["state_dict"].items()}
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device).eval()
    tokenizer = AutoTokenizer.from_pretrained(saved["model_name"])
    return model, tokenizer


def embedSequences(esm, sequences, batch_size=8):
    # mean of the per-residue representations, without the <cls> and <eos> tokens
    import torch

    model, tokenizer = esm
    device = next(model.parameters()).device
    reps = []
    with torch.no_grad():
        for start in range(0, len(sequences), batch_size):
            batch = list(sequences[start : start + batch_size])
            inputs = tokenizer(
                batch, return_tensors="pt", padding=True, truncation=True
            ).to(device)
            hidden = model(**inputs).last_hidden_state
            mask = inputs["attention_mask"].clone()
            mask[:, 0] = 0
            mask[torch.arange(len(batch)), inputs["attention_mask"].sum(1) - 1] = 0
            mask = mask.unsqueeze(-1).to(hidden.dtype)
            reps.append(((hidden * mask).sum(1) / mask.sum(1)).cpu().numpy())
    return np.concatenate(reps)
