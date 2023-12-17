"""python wheel for aria2 static build."""

# DO NOT EDIT THE `__version__` MANUALLY.
# Use `hatch version {new_version}` instead.
# Refer to `CONTRIBUTING.md` for more info.
__version__ = "0.0.1b0"


import logging
import os
import signal
import sys
from pathlib import Path
from subprocess import Popen
from typing import Any, Iterable, NoReturn, Optional

__all__ = ("ARIA2C", "main")


CWD = Path(__file__).parent.absolute()
# NOTE: keep the `bin dir` consistent with the one in `hatch_build.py`
BIN = CWD / "bin"
ARIA2C = BIN / ("aria2c.exe" if sys.platform == "win32" else "aria2c")
"""aria2c binary executable file path."""


CONSOLE_SIGNALS = (signal.SIGINT,)  # Unix signal 2. Sent by Ctrl+C.
if sys.platform == "win32":
    CONSOLE_SIGNALS += (  # Windows signal 21. Sent by Ctrl+Break.  # pyright: ignore[reportConstantRedefinition]
        signal.SIGBREAK,
    )

CLI_SIGNALS = (signal.SIGTERM,)  # Unix signal 15. Sent by `kill <pid>`.


_logger = logging.info


def main(argv: Optional[Iterable[str]] = None) -> NoReturn:
    """Launch aria2c as a subprocess.

    Args:
        argv: The command line arguments that will be passed to aria2c.
            If `None`, `sys.argv[1:]` will be used.

    Raises:
        RuntimeError: If aria2c binary not found.

    Returns:
        Never return, always call `sys.exit()` with the same exit code as aria2c subprocess.
    """
    if not ARIA2C.is_file():
        raise RuntimeError(f"aria2c binary not found: {ARIA2C}")

    # 让ctrl + break 也和 ctrl + c 一样引发 KeyboardInterrupt
    # 请注意，只在 __main__ 中修改，否则会影响 import 此模块的python主进程
    for sig in CONSOLE_SIGNALS:
        signal.signal(sig, signal.getsignal(signal.SIGINT))

    if argv is None:
        argv = sys.argv[1:]

    _logger(f"launch argv: {argv}")
    _logger(f"python pid: {os.getpid()}")
    with Popen([str(ARIA2C), *argv]) as aria2_subprocess:
        _logger(f"aria2c pid: {aria2_subprocess.pid}")

        def _handle_cli_signals(sig: int, _frame: Any) -> None:
            _logger(
                f"python receive signal: {sig}; will send it to aria2c subprocess(pid: {aria2_subprocess.pid})"
            )
            aria2_subprocess.send_signal(sig)

        for _sig in CLI_SIGNALS:
            signal.signal(_sig, _handle_cli_signals)

        while True:
            try:
                sys.exit(aria2_subprocess.wait())
            except KeyboardInterrupt:
                pass

        # 接下来不做任何异常处理，而是由 with 语句来做
