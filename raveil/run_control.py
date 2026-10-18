"""Cooperative control for one foreground array run, never saved-proof authority."""
from contextlib import contextmanager
from contextvars import ContextVar
import json
import math
import signal
import subprocess
import time

_ACTIVE = ContextVar('raveil_array_control', default=None)
_LOCAL = ContextVar('raveil_coupled_deadline', default=None)


class Stopped(BaseException):
    """Bypass ordinary child-failure conversion; unwind all owned writers first."""
    def __init__(self, reason, code):
        self.reason, self.code = reason, code
        super().__init__(reason)


class Control:
    def __init__(self, timeout=None, stream=None):
        if timeout is not None and (type(timeout) not in (int, float) or
                not math.isfinite(timeout) or not .01 <= timeout <= 86400):
            raise ValueError('timeout must be finite, from 0.01 to 86400 seconds')
        self.start = time.monotonic()
        self.deadline = None if timeout is None else self.start + timeout
        self.stream = stream
        self.requested = None
        self.attempt = None
        self.phase = 'preflight'
        self.committed = False

    def request(self, signum=signal.SIGINT, frame=None):
        if self.requested is None:
            self.requested = Stopped('cancelled' if signum == signal.SIGINT else 'terminated', 128+signum)

    def check(self):
        if self.committed: return
        if self.requested is not None: raise self.requested
        now = time.monotonic()
        if self.deadline is not None and now >= self.deadline:
            raise Stopped('overall timeout', 124)
        local = _LOCAL.get()
        if local is not None and now >= local:
            raise Stopped('coupled job timeout', 124)

    def event(self, phase, **fields):
        self.phase = phase
        self.check()
        if self.stream is not None:
            self.stream.write(json.dumps(dict(event=phase, attempt=self.attempt,
                elapsed_seconds=round(time.monotonic()-self.start, 3), **fields), sort_keys=True)+'\n')
            self.stream.flush()

    @contextmanager
    def active(self, *, signals=False):
        token = _ACTIVE.set(self); previous = {}
        try:
            if signals:
                for signum in (signal.SIGINT, signal.SIGTERM):
                    previous[signum] = signal.signal(signum, self.request)
            self.check()
            yield self
        finally:
            for signum, handler in previous.items(): signal.signal(signum, handler)
            _ACTIVE.reset(token)

    def diagnostic(self, error):
        return dict(status='stopped', reason=str(error), phase=self.phase, attempt=self.attempt,
                    outputs=None, recovery='Keep the captured attempt unchanged; retry as a fresh run.')


def current(): return _ACTIVE.get()


def checkpoint():
    control = current()
    if control is not None: control.check()


def event(phase, **fields):
    control = current()
    if control is not None: control.event(phase, **fields)


@contextmanager
def coupled_deadline(deadline):
    token = _LOCAL.set(deadline)
    try:
        checkpoint()
        yield
        checkpoint()
    finally: _LOCAL.reset(token)


def wait(process, timeout):
    """Poll only execution; caller's finally owns bounded, uncancellable cleanup."""
    if current() is None: return process.wait(timeout=timeout)
    end = time.monotonic()+timeout
    while True:
        checkpoint()
        remaining = end-time.monotonic()
        if remaining <= 0: raise Stopped('process wait timeout', 124)
        try:
            code = process.wait(timeout=min(.1, remaining))
        except subprocess.TimeoutExpired: continue
        checkpoint()
        return code


def version(command):
    """Bounded version probe; stop requests cannot strand the owned probe process."""
    if current() is None: return subprocess.check_output(command, text=True, timeout=15)
    checkpoint()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    end = time.monotonic()+15
    try:
        while True:
            checkpoint()
            if time.monotonic() >= end: raise Stopped('QEMU version probe timeout', 124)
            try: out, err = process.communicate(timeout=.1)
            except subprocess.TimeoutExpired: continue
            checkpoint()
            if process.returncode: raise subprocess.CalledProcessError(process.returncode, command, out, err)
            return out
    finally:
        try:
            if process.poll() is None:
                process.kill(); process.wait(timeout=2)
        except BaseException as error:
            from .project_fold import CleanupUncertain
            raise CleanupUncertain('QEMU version probe cleanup could not be verified') from error
        finally:
            if process.stdout: process.stdout.close()
            if process.stderr: process.stderr.close()
