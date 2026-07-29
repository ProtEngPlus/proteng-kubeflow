from pydantic import BaseModel
from typing import Optional


class MMseqs2Params(BaseModel):
    sequence: Optional[str] = ""
    max_seqs: Optional[int] = 50
    e: Optional[float] = 10.0
    min_seq_id: Optional[float] = 0.0
    min_aln_len: Optional[int] = 0
    cov_mode: Optional[int] = 0
    c: Optional[float] = (0.0,)
    seq_length: Optional[int] = 100
    random_state: Optional[int] = 2023


class RequestMMseqs2Body(BaseModel):
    job_id: str
    query_result_id: str
    input: str
    config: MMseqs2Params
    meta: list[str]
