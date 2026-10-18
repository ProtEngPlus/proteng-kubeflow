import asyncio
import contextlib
import signal


def install_sigterm_handler(stop):
    signal.signal(signal.SIGTERM, lambda signum, frame: stop.set())


async def run_until_stopped(consume, stop, poll_seconds=1):
    consuming = asyncio.create_task(consume)
    stopping = asyncio.create_task(_wait_for(stop, poll_seconds))
    done, _ = await asyncio.wait(
        {consuming, stopping}, return_when=asyncio.FIRST_COMPLETED
    )
    if stopping in done:
        consuming.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await consuming
        return True
    stopping.cancel()
    consuming.result()
    return False


async def _wait_for(stop, poll_seconds):
    while not stop.is_set():
        await asyncio.sleep(poll_seconds)
