import os
import threading


class JobTracker:
    def __init__(self, status_path=".active_jobs"):
        self._status_path = status_path
        self._lock = threading.Lock()
        self._idle = threading.Condition(self._lock)
        self._active = 0
        self._write()

    def start(self, target, args=()):
        with self._lock:
            self._active += 1
            self._write()
        thread = threading.Thread(target=self._run, args=(target, args))
        try:
            thread.start()
        except Exception:
            self._finish()
            raise
        return thread

    def active(self):
        with self._lock:
            return self._active

    def wait(self, timeout=None):
        with self._lock:
            return self._idle.wait_for(lambda: self._active == 0, timeout)

    def _run(self, target, args):
        try:
            target(*args)
        finally:
            self._finish()

    def _finish(self):
        with self._lock:
            self._active -= 1
            self._write()
            self._idle.notify_all()

    def _write(self):
        tmp = f"{self._status_path}.tmp"
        with open(tmp, "w") as f:
            f.write(f"{self._active}\n")
        os.replace(tmp, self._status_path)
