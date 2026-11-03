import pandas as pd


def filter_hits(df: pd.DataFrame, seq_length: int) -> tuple[pd.DataFrame, bool]:
    covered = df.dropna(subset=["query_cover"])
    hits = covered[covered["length"] <= seq_length]
    if hits.empty:
        return covered, True
    return hits, False
