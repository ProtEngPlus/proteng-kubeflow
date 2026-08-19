from pydantic import BaseModel

NCBI_BLAST_URL = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"


class BlastParams(BaseModel):
    program: str
    database: str
    sequence: str | None = ""
    url_base: str | None = NCBI_BLAST_URL
    auto_format: bool | None = None
    composition_based_statistics: str | None = None
    db_genetic_code: int | None = None
    endpoints: int | None = None
    entrez_query: str | None = "(none)"
    expect: float | None = 10.0
    filter: str | None = None
    gapcosts: str | None = None
    genetic_code: int | None = None
    hitlist_size: int | None = 50
    i_thresh: float | None = None
    layout: str | None = None
    lcase_mask: int | None = None
    matrix_name: str | None = None
    nucl_penalty: int | None = None
    nucl_reward: int | None = None
    other_advanced: str | None = None
    perc_ident: int | None = None
    phi_pattern: str | None = None
    query_file: str | None = None
    query_believe_defline: bool | None = None
    query_from: int | None = None
    query_to: int | None = None
    searchsp_eff: str | None = None
    service: str | None = None
    threshold: int | None = None
    ungapped_alignment: bool | None = None
    word_size: int | None = None
    short_query: int | None = None
    alignments: int | None = 500
    alignment_view: str | None = None
    descriptions: int | None = 500
    entrez_links_new_window: bool | None = None
    expect_low: float | None = None
    expect_high: float | None = None
    format_entrez_query: str | None = None
    format_object: str | None = None
    format_type: str | None = "XML"
    ncbi_gi: bool | None = None
    results_file: str | None = None
    show_overview: bool | None = None
    megablast: bool | None = None
    template_type: str | None = None
    template_length: int | None = None
    username: str | None = "blast"
    password: str | None = None
    hsp_cov: int | None = 0
    random_state: int | None = 2023
    seq_length: int | None = (100,)


class RequestBlastBody(BaseModel):
    job_id: str
    query_result_id: str
    input: str
    config: BlastParams
    meta: list[str]
