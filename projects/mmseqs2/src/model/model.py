from pydantic import BaseModel
from typing import Optional

class MMseqs2Params(BaseModel):
    sequence: Optional[str] = ""
    expect: Optional[float] = 10.0
    hitlist_size: Optional[int] = 50
    hsp_cov : Optional[int] = 0
    perc_ident: Optional[int] = None
    random_state: Optional[int] = 2023
    seq_length: Optional[int] = 100,


class RequestMMseqs2Body(BaseModel):
    job_id: str
    query_result_id: str
    input: str
    config: MMseqs2Params
    meta: list[str]
