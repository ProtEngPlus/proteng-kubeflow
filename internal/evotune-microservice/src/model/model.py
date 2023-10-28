from pydantic import BaseModel, HttpUrl

class EpochsConfig(BaseModel):
    low:  int
    high: int

class LrConfig(BaseModel):
    low:  float
    high: float

class EvotuneParams(BaseModel):
    n_trials: int | None = 2
    n_splits: int | None = 2
    n_epochs_config: EpochsConfig | None = {"low":1, "high":1}
    learning_rate_config: LrConfig | None = {"low":1e-5, "high":1e-3}

class RequestEvotuneBody(BaseModel):
    job_id: str
    dataset_url: HttpUrl
    evotuned_weights_url: HttpUrl
    evotune_params: EvotuneParams