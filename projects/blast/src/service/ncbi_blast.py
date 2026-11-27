import logging
import os
import re
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

logger = logging.getLogger("blast_service")

NCBI_BLAST_URL = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
PROGRAMS = {"blastn", "blastp", "blastx", "tblastn", "tblastx"}
GET_FIELDS = {
    "alignments",
    "alignment_view",
    "descriptions",
    "entrez_links_new_window",
    "expect_low",
    "expect_high",
    "format_entrez_query",
    "format_object",
    "format_type",
    "ncbi_gi",
    "results_file",
    "service",
    "show_overview",
}
NOT_SENT = {"url_base", "username", "password"}
RENAMED = {"sequence": "QUERY", "short_query": "SHORT_QUERY_ADJUST"}

POLL_SECONDS = 60
REQUEST_GAP_SECONDS = 10
REQUEST_TIMEOUT_SECONDS = 180
MAX_POLL_ERRORS = 3
DEADLINE_SECONDS = int(os.getenv("BLAST_DEADLINE_MINUTES", "90")) * 60

_request_lock = threading.Lock()
_last_request = 0.0


def put_parameters(params: dict) -> dict:
    if params.get("program") not in PROGRAMS:
        raise ValueError(f"unsupported BLAST program {params.get('program')!r}")
    put = {
        RENAMED.get(key, key.upper()): value
        for key, value in params.items()
        if value is not None
        and key not in NOT_SENT
        and (key not in GET_FIELDS or key == "service")
    }
    return {**put, "CMD": "Put"}


def get_parameters(params: dict, rid: str) -> dict:
    get = {
        key.upper(): value
        for key, value in params.items()
        if value is not None and key in GET_FIELDS
    }
    return {**get, "RID": rid, "CMD": "Get"}


def parse_rid(text: str) -> str | None:
    match = re.search(r"^\s*RID = (\S+)", text, re.MULTILINE)
    return match.group(1) if match else None


def parse_status(text: str) -> str | None:
    match = re.search(r"^\s*Status=(\w+)", text, re.MULTILINE)
    return match.group(1).upper() if match else None


def search_blast(
    params: dict,
    job_id: str,
    post=None,
    sleep=time.sleep,
    clock=time.monotonic,
    deadline_seconds: int = DEADLINE_SECONDS,
) -> str:
    post = post or _post
    rid = parse_rid(post(put_parameters(params)))
    if rid is None:
        raise RuntimeError("NCBI BLAST did not return a request id")
    logger.info(f"job id {job_id}: NCBI BLAST RID {rid}")
    wait_until_ready(rid, post, sleep, clock, deadline_seconds)
    return post(get_parameters(params, rid))


def wait_until_ready(rid, post, sleep, clock, deadline_seconds):
    give_up_at = clock() + deadline_seconds
    errors = 0
    while clock() < give_up_at:
        sleep(POLL_SECONDS)
        try:
            text = post({"CMD": "Get", "FORMAT_OBJECT": "SearchInfo", "RID": rid})
        except OSError as err:
            errors += 1
            if errors >= MAX_POLL_ERRORS:
                raise
            logger.warning(f"NCBI BLAST RID {rid}: poll failed, retrying: {err}")
            continue
        errors = 0
        status = parse_status(text)
        if status == "READY":
            return
        if status in ("FAILED", "UNKNOWN"):
            raise RuntimeError(f"NCBI BLAST RID {rid} returned Status={status}")
    raise TimeoutError(
        f"NCBI BLAST RID {rid} not ready after {deadline_seconds // 60} minutes"
    )


def _post(params: dict) -> str:
    global _last_request
    with _request_lock:
        wait = _last_request + REQUEST_GAP_SECONDS - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
    identity = {"tool": "protengplus"}
    email = os.getenv("NCBI_EMAIL")
    if email:
        identity["email"] = email
    body = urlencode({**params, **identity}).encode()
    request = Request(NCBI_BLAST_URL, body, {"User-Agent": "protengplus"})
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return response.read().decode()
