from pydantic import BaseModel, HttpUrl
from typing import Optional

class RequestBucketBody(BaseModel):
    bucket_name: str
    file_name: str | None 
    file: str | None
    
class ArtifactPath(BaseModel):
    bucket_name: str
    path: str
    
class ArtifactMap(BaseModel):
    blast: ArtifactPath
    
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
    
class EvotuneESMParams(BaseModel):
    # n_trials: int | None = 2
    # n_splits: int | None = 2
    n_epochs_config: int | None = 1
    learning_rate_config: float | None = 1e-5
    weight_decay: float | None = 0.01
    
class RequestEvotuneESMBody(BaseModel):
    job_id: str
    input: str
    config: EvotuneESMParams
    artifact: ArtifactMap
    meta: list[str]
    query_result: list[QueryResult]