from pydantic import BaseModel

class ArtifactPath(BaseModel):
    bucket_name: str
    path: str

class ArtifactMap(BaseModel):
    unirep: ArtifactPath
    ridgecv: ArtifactPath

class MutationParams(BaseModel):
    temperature: float      # determines sensitivity of Metropolis-Hastings acceptance criteria
    num_iterations: int     # how many subsequent mutation trials per simulated evolution trajectory
    num_trajectories: int   # how many separate evolution trajectories to run
    mutate_pos_range: int   # where the next mutation is located

class RequestMutationBody(BaseModel):
    job_id: str
    input: str
    mutation_id: str
    config: MutationParams
    artifact: ArtifactMap
    meta: list[str]