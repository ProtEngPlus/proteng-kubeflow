import os
import tempfile
import threading
import unittest

from pkg.common.jobs import JobTracker


class JobTrackerTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, ".active_jobs")

    def tearDown(self):
        self.dir.cleanup()

    def read_file(self):
        with open(self.path) as f:
            return f.read().strip()

    def test_starts_idle(self):
        tracker = JobTracker(self.path)
        self.assertEqual(tracker.active(), 0)
        self.assertEqual(self.read_file(), "0")
        self.assertTrue(tracker.wait(timeout=0))

    def test_counts_running_jobs(self):
        tracker = JobTracker(self.path)
        release = threading.Event()
        tracker.start(release.wait)
        tracker.start(release.wait)
        self.assertEqual(tracker.active(), 2)
        self.assertEqual(self.read_file(), "2")
        release.set()
        self.assertTrue(tracker.wait(timeout=5))
        self.assertEqual(self.read_file(), "0")

    def test_failed_job_is_still_counted_down(self):
        tracker = JobTracker(self.path)
        original_hook = threading.excepthook
        threading.excepthook = lambda args: None
        try:
            tracker.start(lambda: 1 / 0).join()
        finally:
            threading.excepthook = original_hook
        self.assertEqual(tracker.active(), 0)
        self.assertEqual(self.read_file(), "0")

    def test_wait_times_out_while_busy(self):
        tracker = JobTracker(self.path)
        release = threading.Event()
        tracker.start(release.wait)
        self.assertFalse(tracker.wait(timeout=0.05))
        release.set()
        self.assertTrue(tracker.wait(timeout=5))

    def test_passes_args_to_target(self):
        tracker = JobTracker(self.path)
        got = []
        tracker.start(got.append, args=("job-1",)).join()
        self.assertEqual(got, ["job-1"])


if __name__ == "__main__":
    unittest.main()
