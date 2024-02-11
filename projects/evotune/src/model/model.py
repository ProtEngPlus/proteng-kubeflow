from pydantic import BaseModel, HttpUrl

class EvotuneParams(BaseModel):
    n_trials: int | None = 2
    n_splits: int | None = 2
    n_epochs_config_low: int | None = 1
    n_epochs_config_high: int | None = 1
    learning_rate_config_low: float | None = 1e-5
    learning_rate_config_high: float | None = 1e-3


class ArtifactPath(BaseModel):
    bucket_name: str
    path: str


class ArtifactMap(BaseModel):
    blast: ArtifactPath


class RequestEvotuneBody(BaseModel):
    job_id: str
    input: str
    config: EvotuneParams
    artifact: ArtifactMap
    meta: list[str]

class RequestBucketBody(BaseModel):
    bucket_name: str
    file_name: str | None 
    file: str | None
