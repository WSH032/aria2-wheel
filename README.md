<!-- The content will be also use in `docs/index.md` by `pymdownx.snippets` -->
<!-- Do not use any **relative link** and  **GitHub-specific syntax** ！-->
<!-- Do not rename or move the file -->

# Aria2 Wheel

<p align="center">
    <em>python wheel for aria2 static build</em>
</p>

| | |
| - | - |
| CI/CD   | [![CI: lint-test]][CI: lint-test#link] [![pre-commit.ci status]][pre-commit.ci status#link] <br> [![CI: docs]][CI: docs#link] [![CI: publish]][CI: publish#link]  |
| Code    | [![codecov]][codecov#link] [![Code style: black]][Code style: black#link] [![Ruff]][Ruff#link] [![Checked with pyright]][Checked with pyright#link] |
| Package | [![PyPI - Version]][PyPI#link] [![PyPI - Downloads]][PyPI#link] [![PyPI - Python Version]][PyPI#link] |
| Meta    | [![Hatch project]][Hatch project#link] [![GitHub License]][GitHub License#link] |

---

Documentation: <https://wsh032.github.io/aria2-wheel/>

Source Code: <https://github.com/WSH032/aria2-wheel/>

---

## Introduction

[aria2](https://github.com/aria2/aria2) is a lightweight multi-protocol & multi-source command-line download utility.

It's easy to install aria2 on Linux (`apt install aria2`), however it's not easy to install aria2 on Windows (at least can't one-click to install).

So I build this python wheel to binding aria2 static build. You can install it by `pip` from `pypi` on Windows.

Now, we support:

- [x] Windows 32bit
- [x] Windows 64bit
- [x] Linux x86_64
- [x] Linux aarch64

## Features

`aria2-wheel` internally bundles the aria2c binary and utilizes the [entry_point](https://setuptools.pypa.io/en/latest/userguide/entry_point.html#console-scripts) technology.

Therefore, it does not modify your system's `PATH` environment variable, and there is no need for `sudo` permissions.

You can completely uninstall it by running `pip uninstall aria2`.

## Credits

- [aria2](https://github.com/aria2/aria2)
    - This project is not `aria2` official project.
- [aria2-static-build](https://github.com/abcfy2/aria2-static-build)
    - The bound aria2 executable file directly comes from `aria2-static-build` project, and `aria2-wheel` assumes no responsibility for your use.
    - The license of `aria2-wheel` project is consistent with `aria2-static-build` project.

check `hatch_build.py` to know how we build the wheel.

## Install

```shell
pip install aria2
```

or install in global environment with [pipx](https://pypa.github.io/pipx/)

```shell
# https://pypa.github.io/pipx/
pipx install aria2
```

## Usage

### cli usage

All api is the same as [aria2](https://aria2.github.io/manual/en/html/aria2c.html)

```shell
aria2c --help
```

or

```shell
python -m aria2c --help
```

`ctrl + c` , `ctrl + break` , `kill <pid>` will work well, even exit code.

### [subprocess.Popen](https://docs.python.org/3/library/subprocess.html)

Do not shutdown the subprocess by `Popen.terminate()` or `Popen.kill()`, which can not shutdown aria2 subprocess properly.

Use following code instead:

```python
import os
import signal
import subprocess
import sys
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


with Popen(args=("aria2c", "--enable-rpc"), **popen_kwargs) as p:
    try:
        # Do whatever you want here.
        ...
    finally:
        # following code can shutdown the subprocess gracefully.
        if sys.platform == "win32":
            # https://stackoverflow.com/questions/44124338/trying-to-implement-signal-ctrl-c-event-in-python3-6
            os.kill(p.pid, signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(os.getpgid(p.pid), signal.SIGINT)
```

## development

- If you find any issues, please don't hesitate to [open an issue](https://github.com/WSH032/aria2-wheel/issues).
- If you need assistance, feel free to [start a discussion](https://github.com/WSH032/aria2-wheel/discussions).
- Follow our `CONTRIBUTING.md`, [PR Welcome!](https://github.com/WSH032/aria2-wheel/pulls)
- Security 😰❗: We value any security vulnerabilities, [please report to us privately](https://github.com/WSH032/aria2-wheel/security), pretty appreciated for that.

English is not the native language of the author (me), so if you find any areas for improvement in the documentation, your feedback is welcome.

If you think this project helpful, consider giving it a star ![GitHub Repo stars](https://img.shields.io/github/stars/wsh032/aria2-wheel?style=social), which makes me happy. :smile:

<!-- link -->

<!-- ci/cd -->
[CI: lint-test]: https://github.com/WSH032/aria2-wheel/actions/workflows/lint-test.yml/badge.svg?branch=main
[CI: lint-test#link]: https://github.com/WSH032/aria2-wheel/actions/workflows/lint-test.yml
[CI: docs]: https://github.com/WSH032/aria2-wheel/actions/workflows/docs.yml/badge.svg?branch=main
[CI: docs#link]: https://github.com/WSH032/aria2-wheel/actions/workflows/docs.yml
[CI: publish]: https://github.com/WSH032/aria2-wheel/actions/workflows/publish.yml/badge.svg
[CI: publish#link]: https://github.com/WSH032/aria2-wheel/actions/workflows/publish.yml
[pre-commit.ci status]: https://results.pre-commit.ci/badge/github/WSH032/aria2-wheel/main.svg
[pre-commit.ci status#link]: https://results.pre-commit.ci/latest/github/WSH032/aria2-wheel/main
<!-- code -->
[Code style: black]: https://img.shields.io/badge/code%20style-black-000000.svg
[Code style: black#link]: https://github.com/psf/black
[GitHub License]: https://img.shields.io/github/license/WSH032/aria2-wheel?color=9400d3
[GitHub License#link]: https://github.com/WSH032/aria2-wheel/blob/main/LICENSE
[Ruff]: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
[Ruff#link]: https://github.com/astral-sh/ruff
[Checked with pyright]: https://microsoft.github.io/pyright/img/pyright_badge.svg
[Checked with pyright#link]: https://microsoft.github.io/pyright
<!-- package -->
[PyPI - Version]: https://img.shields.io/pypi/v/aria2-wheel?logo=pypi&label=PyPI&logoColor=gold
[PyPI - Downloads]: https://img.shields.io/pypi/dm/aria2-wheel?color=blue&label=Downloads&logo=pypi&logoColor=gold
[PyPI - Python Version]: https://img.shields.io/pypi/pyversions/aria2-wheel?logo=python&label=Python&logoColor=gold
[PyPI#link]: https://pypi.org/project/aria2-wheel
<!-- meta -->
[Hatch project]: https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg
[Hatch project#link]: https://github.com/pypa/hatch
[codecov]: https://codecov.io/gh/WSH032/aria2-wheel/graph/badge.svg?token=62QQU06E8X
[codecov#link]: https://codecov.io/gh/WSH032/aria2-wheel
