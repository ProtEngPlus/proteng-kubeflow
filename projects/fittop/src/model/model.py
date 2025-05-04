from pydantic import BaseModel
from typing import Dict, List

class FitTopParams(BaseModel):
    train_batch_sizes: list[int] | None = [24, 64, 96]
    n_batch: int | None = 20
    alpha: float | None = 0.01

class ArtifactPath(BaseModel):
    bucket_name: str
    path: str

class ArtifactMap(BaseModel):
    unirep: ArtifactPath

class LabResult(BaseModel):
    total: int
    sequences: list[str]
    scores: list[float]

class RequestFitTopBody(BaseModel):
    job_id: str
    input: str
    config: FitTopParams
    artifact: Dict[str, ArtifactPath]
    lab_result: LabResult
    meta: list[str]