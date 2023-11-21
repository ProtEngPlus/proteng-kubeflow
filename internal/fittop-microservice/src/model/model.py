from pydantic import BaseModel, HttpUrl

class FitTopParams(BaseModel):
    TRAIN_BATCH_SIZES: list[int] | None = [24, 64, 96]
    N_BATCH: int | None = 20
    N_RAND_BATCHES: int | None = 20
    WT_FIT: float | None = 0.63481905
    ALPHA: float | None = 0.01

class ArtifactPath(BaseModel):
    bucket_name: str
    path: str

class UnirepArtifactPath(BaseModel):
    bucket_name: str | None = 'unirep'
    path: str | None = "123/1.pkl"

class ArtifactMap(BaseModel):
    unirep: UnirepArtifactPath
    fittop: ArtifactPath

class RequestFitTopBody(BaseModel):
    job_id: str
    input: str
    config: FitTopParams
    artifact: ArtifactMap
    meta: list[str]