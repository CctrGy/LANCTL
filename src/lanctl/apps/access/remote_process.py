"""Bounded incremental stdout/stderr capture without temporary files or readers."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from concurrent.futures import CancelledError
from contextlib import suppress


def bounded_run(
    command,
    *,
    timeout,
    env=None,
    stdin=subprocess.DEVNULL,
    shell=False,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    max_output=1024 * 1024,
    cancel_event=None,
):
    """Drain both pipes; retain at most max_output bytes in aggregate.

    Excess output is discarded until exit or deadline. Nonblocking anonymous
    pipes are supported on Windows with Python 3.12+ and on POSIX. A failure
    to configure them fails closed rather than falling back to unlimited capture.
    """
    deadline = time.monotonic() + timeout
    process = subprocess.Popen(
        command,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=stdin,
        env=env,
        bufsize=0,
        start_new_session=os.name != "nt",
    )
    streams = (process.stdout, process.stderr)
    retained = [bytearray(), bytearray()]
    size, truncated = 0, False
    try:
        pending = dict(enumerate(streams))
        for stream in streams:
            os.set_blocking(stream.fileno(), False)
        while pending or process.poll() is None:
            if cancel_event is not None and cancel_event.is_set():
                raise CancelledError()
            if time.monotonic() >= deadline:
                # Do not attach captured output to exceptions/logs.
                raise subprocess.TimeoutExpired(command, timeout)
            received = False
            for index, stream in tuple(pending.items()):
                try:
                    chunk = os.read(stream.fileno(), 16384)
                except BlockingIOError:
                    continue
                if not chunk:
                    del pending[index]
                    continue
                received = True
                available = max(0, max_output - size)
                kept = chunk[:available]
                retained[index].extend(kept)
                size += len(kept)
                truncated |= len(kept) != len(chunk)
            if not received:
                time.sleep(min(0.01, max(0, deadline - time.monotonic())))
        result = subprocess.CompletedProcess(
            command,
            process.returncode,
            retained[0].decode(encoding, errors) if text else bytes(retained[0]),
            retained[1].decode(encoding, errors) if text else bytes(retained[1]),
        )
        result.truncated = truncated
        return result
    finally:
        try:
            if os.name != "nt":
                # This group belongs exclusively to this invocation, including
                # descendants that inherited pipes after their parent exited.
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
            elif process.poll() is None:
                process.kill()
        finally:
            for stream in streams:
                stream.close()
            process.wait()
