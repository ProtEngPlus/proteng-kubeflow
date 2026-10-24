import unittest

import pandas as pd
from src.service.hit_filter import filter_hits


def make_df(rows):
    return pd.DataFrame(rows, columns=["length", "query_cover"])


class FilterHitsTest(unittest.TestCase):
    def test_keeps_covered_hits_shorter_than_seq_length(self):
        df = make_df([(50, 90.0), (150, 90.0), (60, 10.0)])
        hits, fell_back = filter_hits(df, hsp_cov=30, seq_length=100)
        self.assertFalse(fell_back)
        self.assertEqual(hits["length"].tolist(), [50])

    def test_falls_back_to_cover_filter_when_no_hit_is_short_enough(self):
        df = make_df([(150, 90.0), (200, 10.0)])
        hits, fell_back = filter_hits(df, hsp_cov=30, seq_length=100)
        self.assertTrue(fell_back)
        self.assertEqual(hits["length"].tolist(), [150])

    def test_drops_hits_without_query_cover(self):
        df = make_df([(50, float("nan")), (60, 90.0)])
        hits, _ = filter_hits(df, hsp_cov=30, seq_length=100)
        self.assertEqual(hits["length"].tolist(), [60])


if __name__ == "__main__":
    unittest.main()
