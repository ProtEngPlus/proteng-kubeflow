from pydantic import BaseModel


class ArtifactPath(BaseModel):
    bucket_name: str
    path: str


class ArtifactMap(BaseModel):
    unirep: ArtifactPath
    ridgecv: ArtifactPath


class MutationParams(BaseModel):
    temperature: (
        float  # determines sensitivity of Metropolis-Hastings acceptance criteria
    )
    num_iterations: (
        int  # how many subsequent mutation trials per simulated evolution trajectory
    )
    num_trajectories: int  # how many separate evolution trajectories to run
    mutate_regions: list[tuple[int, int]] | None = None  # [start, end], 1-based
    num_mutations_low: int = 1  # fewest mutated positions per sequence
    num_mutations_high: int = 3  # most mutated positions per sequence
    amino_acid_set: str = "20 standard"  # which amino acids a position can mutate to


class RequestMutationBody(BaseModel):
    job_id: str
    input: str
    mutation_id: str
    config: MutationParams
    artifact: dict[str, ArtifactPath]
    meta: list[str]
