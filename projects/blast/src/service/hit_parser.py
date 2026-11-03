import io
import os
import re

import pandas as pd
from Bio import Entrez, SeqIO
from Bio.Blast import NCBIXML

Entrez.email = os.getenv("NCBI_EMAIL")
Entrez.tool = "protengplus"

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


def fetch_fasta(accessions: list[str]) -> str:
    with Entrez.efetch(
        db="protein", id=",".join(accessions), rettype="fasta", retmode="text"
    ) as handle:
        return handle.read()


def parse_fasta_by_accession(fasta_text: str) -> dict[str, str]:
    return {
        accession_key(record.id): str(record.seq)
        for record in SeqIO.parse(io.StringIO(fasta_text), "fasta")
    }


def attach_full_sequences(
    df: pd.DataFrame, full: dict[str, str]
) -> tuple[pd.DataFrame, int]:
    df = df.copy()
    df["sequences"] = df["accession"].map(lambda a: full.get(accession_key(a)))
    kept = df.dropna(subset=["sequences"])
    return kept, len(df) - len(kept)


def accession_key(seq_id: str) -> str:
    parts = seq_id.split("|")
    accession = parts[1] if len(parts) > 1 else parts[0]
    return accession.split(".")[0]


def extract_protein_info(hit_def):
    return re.split(r"\s?\[", hit_def)[0].strip()


def extract_organism(hit_def):
    matches = re.findall(r"\[([^\]]+)\]", hit_def)
    return matches[0] if matches else "Unknown"
