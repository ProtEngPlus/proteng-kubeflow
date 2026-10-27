from typing import Any

from pydantic import BaseModel, Field


class Protein(BaseModel):
    sequence: str


class EvaluationMutant(BaseModel):
    mutation_result_id: str
    sequence: str
    assay_score: float


class RequestEvaluationBody(BaseModel):
    job_id: str
    evaluation_run_id: str
    plugin: str
    wild_type: Protein
    mutants: list[EvaluationMutant]
    config: dict[str, Any] = Field(default_factory=dict)
