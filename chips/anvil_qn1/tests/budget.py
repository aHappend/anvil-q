"""One whole-check deadline, including Python preparation and receipt retention.

The soft deadline reserves 50 seconds for settling children and retaining failure
receipts. Children share the original clock; neither nesting nor reuse renews it.
This changes execution limits, not arithmetic or retained-component applicability.
"""

from contextlib import contextmanager
from pathlib import Path
import signal
import threading
import time

import execution


START = time.monotonic()
LIMIT = 2700
RESERVE = 50


class BudgetExceeded(TimeoutError):
    pass


def remaining(retention=False):
    return max(0.0, START + LIMIT - (0 if retention else RESERVE) - time.monotonic())


def expired(signum, frame):
    raise BudgetExceeded("cumulative whole-check budget exhausted")


@contextmanager
def whole_check():
    old_handler = signal.signal(signal.SIGALRM, expired)
    old_timer = signal.setitimer(signal.ITIMER_REAL, max(0.001, remaining()))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
        if old_timer[0]:
            signal.setitimer(signal.ITIMER_REAL, *old_timer)


BaseRun = execution.Run


class Run(BaseRun):
    def __init__(self, *args, **kwargs):
        if remaining() <= 0:
            raise BudgetExceeded("whole-check budget exhausted before source retention")
        super().__init__(*args, **kwargs)
        self.monotonic_start = START

    def execute(self, argv, name, timeout=2700, **kwargs):
        allowance = remaining()
        if allowance <= 0:
            raise BudgetExceeded(f"whole-check budget exhausted before {name}")
        if Path(str(argv[0])).name == "vvp":
            allowance = min(allowance, 600)
        main_thread = threading.current_thread() is threading.main_thread()
        timer = signal.setitimer(signal.ITIMER_REAL, 0) if main_thread else (0, 0)
        first_command = len(self.commands)
        try:
            return super().execute(argv, name, timeout=min(timeout, allowance), **kwargs)
        finally:
            for record in self.commands[first_command:]:
                record["expected_exit"] = kwargs.get("expected_exit", 0)
            if timer[0]:
                signal.setitimer(signal.ITIMER_REAL, max(0.001, remaining()))

    def finish(self, status, results=None, error=None):
        if threading.current_thread() is not threading.main_thread():
            if remaining(retention=True) <= 0:
                raise BudgetExceeded("whole-check retention deadline exceeded")
            if remaining() <= 0:
                status, results, error = "failed", None, "whole-check preparation deadline exceeded"
            super().finish(status, results, error)
            return status
        timer = signal.setitimer(signal.ITIMER_REAL, 0)
        try:
            retention_allowance = remaining(retention=True)
            if retention_allowance <= 0:
                raise BudgetExceeded("whole-check retention deadline exceeded")
            signal.setitimer(signal.ITIMER_REAL, retention_allowance)
            if remaining() <= 0:
                status, results, error = "failed", None, "whole-check preparation deadline exceeded"
            super().finish(status, results, error)
            return status
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            if timer[0]:
                signal.setitimer(signal.ITIMER_REAL, max(0.001, remaining()))


# BaseRun.component resolves its child class in execution's module namespace.
execution.Run = Run
