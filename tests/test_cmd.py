# noqa: D100

import os
import signal
import socket
import subprocess
import sys
import time
from subprocess import Popen
from typing import TypedDict


class Win32PopenKwargs(TypedDict):
    """Popen kwargs for Windows."""

    creationflags: int


class UnixPopenKwargs(TypedDict):
    """Popen kwargs for Unix."""

    start_new_session: bool


popen_kwargs = (
    UnixPopenKwargs(start_new_session=True)
    if sys.platform != "win32"
    else Win32PopenKwargs(creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
)


def get_free_port() -> int:
    """Get a free port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("localhost", 0))
    _address, port = s.getsockname()
    return port


def test_help() -> None:
    """Test `aria2c --help`."""
    with Popen(
        args=("aria2c", "--help"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **popen_kwargs,
    ) as p:
        outs, errs = p.communicate()
        assert not errs
        assert outs.startswith(b"Usage: aria2c")
        assert p.wait() == 0


def test_rpc() -> None:
    """Test `aria2c --enable-rpc`."""
    with Popen(
        args=(
            "aria2c",
            "--enable-rpc",
            f"--rpc-listen-port={get_free_port()}",
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **popen_kwargs,
    ) as p:
        time.sleep(1)  # wait for aria2c to start
        if sys.platform == "win32":
            # https://stackoverflow.com/questions/44124338/trying-to-implement-signal-ctrl-c-event-in-python3-6
            os.kill(p.pid, signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(os.getpgid(p.pid), signal.SIGINT)
        outs, errs = p.communicate()
        assert not errs
        assert b"Press Ctrl-C again for emergency shutdown" in outs
        assert p.wait() == 0


if sys.platform != "win32":

    def test_terminate_subprocess() -> None:
        """Test terminate subprocess."""
        with Popen(
            args=(
                "aria2c",
                "--enable-rpc",
                f"--rpc-listen-port={get_free_port()}",
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **popen_kwargs,
        ) as p:
            time.sleep(1)  # wait for aria2c to start
            p.terminate()
            outs, errs = p.communicate()
            assert not errs
            assert b"Emergency shutdown sequence commencing" in outs
            assert p.wait() == 0
