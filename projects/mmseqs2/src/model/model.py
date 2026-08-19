from pydantic import BaseModel


class MMseqs2Params(BaseModel):
    sequence: str | None = ""
    max_seqs: int | None = 50
    e: float | None = 10.0
    min_seq_id: float | None = 0.0
    min_aln_len: int | None = 0
    cov_mode: int | None = 0
    c: float | None = (0.0,)
    seq_length: int | None = 100
    random_state: int | None = 2023


class RequestMMseqs2Body(BaseModel):
    job_id: str
    query_result_id: str
    input: str
    config: MMseqs2Params
    meta: list[str]
