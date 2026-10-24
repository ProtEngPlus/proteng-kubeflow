import io
import re

import pandas as pd
from Bio.Blast import NCBIXML

COLUMNS = [
    "sequences",
    "score",
    "max_score",
    "hsp_query_from",
    "hsp_query_to",
    "e_values",
    "accession",
    "percent_identity",
    "acc_len",
    "description",
    "organisms",
]


def parse_hits(xml_text: str) -> pd.DataFrame:
    record = NCBIXML.read(io.StringIO(xml_text))
    rows = []
    for alignment in record.alignments:
        hsp = alignment.hsps[0]
        rows.append(
            {
                "sequences": hsp.sbjct,
                "score": hsp.score,
                "max_score": hsp.bits,
                "hsp_query_from": hsp.query_start,
                "hsp_query_to": hsp.query_end,
                "e_values": hsp.expect,
                "accession": alignment.accession,
                "percent_identity": hsp.identities / hsp.align_length * 100,
                "acc_len": alignment.length,
                "description": extract_protein_info(alignment.hit_def),
                "organisms": extract_organism(alignment.hit_def),
            }
        )
    return pd.DataFrame(rows, columns=COLUMNS)


def extract_protein_info(hit_def):
    return re.split(r"\s?\[", hit_def)[0].strip()


def extract_organism(hit_def):
    matches = re.findall(r"\[([^\]]+)\]", hit_def)
    return matches[0] if matches else "Unknown"
