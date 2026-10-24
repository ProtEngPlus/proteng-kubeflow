import pandas as pd


def filter_hits(
    df: pd.DataFrame, hsp_cov: int, seq_length: int
) -> tuple[pd.DataFrame, bool]:
    covered = df[df["query_cover"] > hsp_cov].dropna(subset=["query_cover"])
    hits = covered[covered["length"] < seq_length]
    if hits.empty:
        return covered, True
    return hits, False
