import asyncio
import signal
import threading
import unittest

from pkg.common.shutdown import install_sigterm_handler, run_until_stopped


class InstallSigtermHandlerTest(unittest.TestCase):
    def test_sigterm_sets_stop(self):
        original = signal.getsignal(signal.SIGTERM)
        self.addCleanup(signal.signal, signal.SIGTERM, original)
        stop = threading.Event()
        install_sigterm_handler(stop)
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        self.assertTrue(stop.is_set())


class RunUntilStoppedTest(unittest.IsolatedAsyncioTestCase):
    async def test_stop_cancels_consumer(self):
        stop = threading.Event()
        cancelled = asyncio.Event()

        async def consume():
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        asyncio.get_running_loop().call_later(0.05, stop.set)
        stopped = await run_until_stopped(consume(), stop, poll_seconds=0.01)
        self.assertTrue(stopped)
        self.assertTrue(cancelled.is_set())

    async def test_consumer_that_ends_is_not_a_stop(self):
        async def consume():
            return None

        stopped = await run_until_stopped(consume(), threading.Event(), 0.01)
        self.assertFalse(stopped)

    async def test_consumer_error_is_raised(self):
        async def consume():
            raise ConnectionError("broker gone")

        with self.assertRaises(ConnectionError):
            await run_until_stopped(consume(), threading.Event(), 0.01)


if __name__ == "__main__":
    unittest.main()
