import unittest

from src.service.ncbi_blast import (
    get_parameters,
    parse_rid,
    parse_status,
    put_parameters,
    search_blast,
)

PARAMS = {
    "program": "blastp",
    "database": "nr",
    "sequence": "MALWMRLLPLLALLALWGPD",
    "url_base": "http://example.invalid/",
    "username": "blast",
    "entrez_query": "(none)",
    "expect": 10.0,
    "hitlist_size": 50,
    "perc_ident": 30,
    "alignments": 500,
    "descriptions": 500,
    "format_type": "XML",
    "matrix_name": None,
}

PUT_PAGE = """<!--QBlastInfoBegin
    RID = EVXU7Y8J014
    RTOE = 26
QBlastInfoEnd
-->"""


def search_info(status):
    return f"<!--\nQBlastInfoBegin\n\tStatus={status}\nQBlastInfoEnd\n-->"


class FakeNcbi:
    def __init__(self, polls, default=search_info("WAITING")):
        self.polls = list(polls)
        self.default = default
        self.now = 0.0
        self.sleeps = []
        self.calls = []

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds

    def clock(self):
        return self.now

    def post(self, params):
        self.calls.append(params)
        if params["CMD"] == "Put":
            return PUT_PAGE
        if params.get("FORMAT_OBJECT") == "SearchInfo":
            reply = self.polls.pop(0) if self.polls else self.default
            if isinstance(reply, Exception):
                raise reply
            return reply
        return "<BlastOutput/>"

    def search(self, deadline_seconds=90 * 60):
        return search_blast(
            PARAMS,
            "job-1",
            post=self.post,
            sleep=self.sleep,
            clock=self.clock,
            deadline_seconds=deadline_seconds,
        )

    def poll_count(self):
        return sum(1 for c in self.calls if c.get("FORMAT_OBJECT") == "SearchInfo")


class ParametersTest(unittest.TestCase):
    def test_put_sends_search_fields_only(self):
        self.assertEqual(
            put_parameters(PARAMS),
            {
                "PROGRAM": "blastp",
                "DATABASE": "nr",
                "QUERY": "MALWMRLLPLLALLALWGPD",
                "ENTREZ_QUERY": "(none)",
                "EXPECT": 10.0,
                "HITLIST_SIZE": 50,
                "PERC_IDENT": 30,
                "CMD": "Put",
            },
        )

    def test_put_rejects_unknown_program(self):
        with self.assertRaises(ValueError):
            put_parameters({**PARAMS, "program": "psiblast"})

    def test_get_sends_format_fields_and_rid(self):
        self.assertEqual(
            get_parameters(PARAMS, "EVXU7Y8J014"),
            {
                "ALIGNMENTS": 500,
                "DESCRIPTIONS": 500,
                "FORMAT_TYPE": "XML",
                "RID": "EVXU7Y8J014",
                "CMD": "Get",
            },
        )


class ParseTest(unittest.TestCase):
    def test_reads_rid_from_put_page(self):
        self.assertEqual(parse_rid(PUT_PAGE), "EVXU7Y8J014")
        self.assertIsNone(parse_rid("<html>error</html>"))

    def test_reads_status_from_search_info(self):
        self.assertEqual(parse_status(search_info("WAITING")), "WAITING")
        self.assertEqual(parse_status(search_info("READY")), "READY")
        self.assertIsNone(parse_status("\n\n"))


class SearchTest(unittest.TestCase):
    def test_returns_result_once_ready(self):
        ncbi = FakeNcbi([search_info("WAITING"), search_info("READY")])
        self.assertEqual(ncbi.search(), "<BlastOutput/>")
        self.assertEqual(ncbi.poll_count(), 2)
        self.assertEqual(ncbi.sleeps, [60, 60])
        self.assertEqual(ncbi.calls[-1]["RID"], "EVXU7Y8J014")

    def test_fails_when_ncbi_reports_failed_or_unknown(self):
        for status in ("FAILED", "UNKNOWN"):
            with self.subTest(status=status):
                ncbi = FakeNcbi([search_info(status)])
                with self.assertRaisesRegex(RuntimeError, status):
                    ncbi.search()

    def test_gives_up_at_the_deadline(self):
        ncbi = FakeNcbi([])
        with self.assertRaises(TimeoutError):
            ncbi.search(deadline_seconds=5 * 60)
        self.assertEqual(ncbi.poll_count(), 5)

    def test_retries_a_failed_poll(self):
        ncbi = FakeNcbi([OSError("proxy"), search_info("READY")])
        self.assertEqual(ncbi.search(), "<BlastOutput/>")

    def test_stops_after_repeated_poll_errors(self):
        ncbi = FakeNcbi([OSError("proxy")] * 3)
        with self.assertRaises(OSError):
            ncbi.search()
        self.assertEqual(ncbi.poll_count(), 3)

    def test_fails_without_rid(self):
        ncbi = FakeNcbi([])
        ncbi.post = lambda params: "<html>Server busy</html>"
        with self.assertRaisesRegex(RuntimeError, "request id"):
            ncbi.search()


if __name__ == "__main__":
    unittest.main()
