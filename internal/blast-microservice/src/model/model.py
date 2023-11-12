from pydantic import BaseModel
from typing import List, Optional

NCBI_BLAST_URL = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"


class BlastParams(BaseModel):
    program: str
    database: str
    sequence: str
    url_base: Optional[str] = NCBI_BLAST_URL
    auto_format: Optional[bool] = None
    composition_based_statistics: Optional[str] = None
    db_genetic_code: Optional[int] = None
    endpoints: Optional[int] = None
    entrez_query: Optional[str] = "(none)"
    expect: Optional[float] = 10.0
    filter: Optional[str] = None
    gapcosts: Optional[str] = None
    genetic_code: Optional[int] = None
    hitlist_size: Optional[int] = 50
    i_thresh: Optional[float] = None
    layout: Optional[str] = None
    lcase_mask: Optional[int] = None
    matrix_name: Optional[str] = None
    nucl_penalty: Optional[int] = None
    nucl_reward: Optional[int] = None
    other_advanced: Optional[str] = None
    perc_ident: Optional[int] = None
    phi_pattern: Optional[str] = None
    query_file: Optional[str] = None
    query_believe_defline: Optional[bool] = None
    query_from: Optional[int] = None
    query_to: Optional[int] = None
    searchsp_eff: Optional[str] = None
    service: Optional[str] = None
    threshold: Optional[int] = None
    ungapped_alignment: Optional[bool] = None
    word_size: Optional[int] = None
    short_query: Optional[int] = None
    alignments: Optional[int] = 500
    alignment_view: Optional[str] = None
    descriptions: Optional[int] = 500
    entrez_links_new_window: Optional[bool] = None
    expect_low: Optional[float] = None
    expect_high: Optional[float] = None
    format_entrez_query: Optional[str] = None
    format_object: Optional[str] = None
    format_type: Optional[str] = "XML"
    ncbi_gi: Optional[bool] = None
    results_file: Optional[str] = None
    show_overview: Optional[bool] = None
    megablast: Optional[bool] = None
    template_type: Optional[str] = None
    template_length: Optional[int] = None
    username: Optional[str] = "blast"
    password: Optional[str] = None


class RequestBody(BaseModel):
    job_id: str
    running_id: str
    random_state: Optional[int] = 2023
    blast_params: BlastParams
