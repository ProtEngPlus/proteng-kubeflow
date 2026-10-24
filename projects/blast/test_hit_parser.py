import unittest

from src.service.hit_parser import parse_hits


def hsp_xml(score, bits, evalue, qfrom, qto, identity, align_len, hseq):
    return f"""
        <Hsp>
          <Hsp_num>1</Hsp_num>
          <Hsp_bit-score>{bits}</Hsp_bit-score>
          <Hsp_score>{score}</Hsp_score>
          <Hsp_evalue>{evalue}</Hsp_evalue>
          <Hsp_query-from>{qfrom}</Hsp_query-from>
          <Hsp_query-to>{qto}</Hsp_query-to>
          <Hsp_hit-from>1</Hsp_hit-from>
          <Hsp_hit-to>{align_len}</Hsp_hit-to>
          <Hsp_identity>{identity}</Hsp_identity>
          <Hsp_positive>{identity}</Hsp_positive>
          <Hsp_gaps>0</Hsp_gaps>
          <Hsp_align-len>{align_len}</Hsp_align-len>
          <Hsp_qseq>{hseq}</Hsp_qseq>
          <Hsp_hseq>{hseq}</Hsp_hseq>
          <Hsp_midline>{hseq}</Hsp_midline>
        </Hsp>"""


def hit_xml(num, accession, hit_def, length, hsps):
    return f"""
    <Hit>
      <Hit_num>{num}</Hit_num>
      <Hit_id>ref|{accession}.1|</Hit_id>
      <Hit_def>{hit_def}</Hit_def>
      <Hit_accession>{accession}</Hit_accession>
      <Hit_len>{length}</Hit_len>
      <Hit_hsps>{"".join(hsps)}
      </Hit_hsps>
    </Hit>"""


def blast_xml(hits):
    return f"""<?xml version="1.0"?>
<!DOCTYPE BlastOutput PUBLIC "-//NCBI//NCBI BlastOutput/EN" "http://www.ncbi.nlm.nih.gov/dtd/NCBI_BlastOutput.dtd">
<BlastOutput>
  <BlastOutput_program>blastp</BlastOutput_program>
  <BlastOutput_version>BLASTP 2.16.0+</BlastOutput_version>
  <BlastOutput_reference>ref</BlastOutput_reference>
  <BlastOutput_db>nr</BlastOutput_db>
  <BlastOutput_query-ID>Query_1</BlastOutput_query-ID>
  <BlastOutput_query-def>unnamed protein product</BlastOutput_query-def>
  <BlastOutput_query-len>20</BlastOutput_query-len>
  <BlastOutput_param>
    <Parameters>
      <Parameters_matrix>BLOSUM62</Parameters_matrix>
      <Parameters_expect>10</Parameters_expect>
      <Parameters_gap-open>11</Parameters_gap-open>
      <Parameters_gap-extend>1</Parameters_gap-extend>
      <Parameters_filter>F</Parameters_filter>
    </Parameters>
  </BlastOutput_param>
  <BlastOutput_iterations>
    <Iteration>
      <Iteration_iter-num>1</Iteration_iter-num>
      <Iteration_query-ID>Query_1</Iteration_query-ID>
      <Iteration_query-def>unnamed protein product</Iteration_query-def>
      <Iteration_query-len>20</Iteration_query-len>
      <Iteration_hits>{"".join(hits)}
      </Iteration_hits>
      <Iteration_stat>
        <Statistics>
          <Statistics_db-num>1</Statistics_db-num>
          <Statistics_db-len>1</Statistics_db-len>
          <Statistics_hsp-len>0</Statistics_hsp-len>
          <Statistics_eff-space>0</Statistics_eff-space>
          <Statistics_kappa>0.041</Statistics_kappa>
          <Statistics_lambda>0.267</Statistics_lambda>
          <Statistics_entropy>0.14</Statistics_entropy>
        </Statistics>
      </Iteration_stat>
    </Iteration>
  </BlastOutput_iterations>
</BlastOutput>
"""


TWO_HITS = blast_xml(
    [
        hit_xml(
            1,
            "XP_000001",
            "kinase A [Homo sapiens] &gt;kinase A [Pan troglodytes]",
            300,
            [
                hsp_xml(100, 45.5, 1e-10, 1, 20, 18, 20, "MKTAYIAKQRQISFVKSHFS"),
                hsp_xml(30, 12.0, 0.5, 5, 10, 5, 6, "AYIAKQ"),
            ],
        ),
        hit_xml(
            2,
            "P69905",
            "hypothetical protein",
            142,
            [hsp_xml(80, 35.0, 1e-5, 3, 18, 12, 16, "TAYIA-QRQISFVKSH")],
        ),
    ]
)


class ParseHitsTest(unittest.TestCase):
    def test_one_row_per_hit_from_its_first_hsp(self):
        df = parse_hits(TWO_HITS)
        self.assertEqual(df["accession"].tolist(), ["XP_000001", "P69905"])
        first = df.iloc[0]
        self.assertEqual(first["sequences"], "MKTAYIAKQRQISFVKSHFS")
        self.assertEqual(first["score"], 100)
        self.assertEqual(first["max_score"], 45.5)
        self.assertEqual(first["hsp_query_from"], 1)
        self.assertEqual(first["hsp_query_to"], 20)
        self.assertEqual(first["e_values"], 1e-10)
        self.assertEqual(first["percent_identity"], 90.0)
        self.assertEqual(first["acc_len"], 300)

    def test_splits_description_and_organism_from_hit_def(self):
        df = parse_hits(TWO_HITS)
        self.assertEqual(
            df["description"].tolist(), ["kinase A", "hypothetical protein"]
        )
        self.assertEqual(df["organisms"].tolist(), ["Homo sapiens", "Unknown"])

    def test_no_hits_gives_empty_frame_with_columns(self):
        df = parse_hits(blast_xml([]))
        self.assertTrue(df.empty)
        self.assertIn("sequences", df.columns)
        self.assertIn("acc_len", df.columns)


if __name__ == "__main__":
    unittest.main()
