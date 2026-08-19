from pydantic import BaseModel


class EvotuneParams(BaseModel):
    n_trials: int | None = 2
    n_splits: int | None = 2
    n_epochs_config_low: int | None = 1
    n_epochs_config_high: int | None = 1
    learning_rate_config_low: float | None = 1e-5
    learning_rate_config_high: float | None = 1e-3


class QueryResult(BaseModel):
    id: str
    is_selected: bool
    sequences: str
    score: float
    max_score: float
    hsp_query_from: float
    hsp_query_to: float
    query_cover: float
    e_values: float
    accession: str
    percent_identity: float
    acc_len: int
    description: str
    organisms: str


class ArtifactPath(BaseModel):
    bucket_name: str
    path: str


class ArtifactMap(BaseModel):
    blast: ArtifactPath | None = None
    mmseqs2: ArtifactPath | None = None


class RequestEvotuneBody(BaseModel):
    job_id: str
    input: str
    config: EvotuneParams
    artifact: ArtifactMap
    meta: list[str]
    query_result: list[QueryResult]


class RequestBucketBody(BaseModel):
    bucket_name: str
    file_name: str | None
    file: str | None
