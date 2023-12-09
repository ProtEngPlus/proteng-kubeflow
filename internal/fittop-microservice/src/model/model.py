from pydantic import BaseModel, HttpUrl

class FitTopParams(BaseModel):
    train_batch_sizes: list[int] | None = [24, 64, 96]
    n_batch: int | None = 20
    n_rand_batches: int | None = 20
    wt_fit: float | None = 0.63481905
    alpha: float | None = 0.01

class ArtifactPath(BaseModel):
    bucket_name: str
    path: str

class UnirepArtifactPath(BaseModel):
    bucket_name: str | None = 'unirep'
    path: str | None = "123/1.pkl"

class ArtifactMap(BaseModel):
    blast: ArtifactPath
    unirep: UnirepArtifactPath

class RequestFitTopBody(BaseModel):
    job_id: str
    input: str
    config: FitTopParams
    artifact: ArtifactMap
    meta: list[str]