"""building script for hatchling.

Ref: https://hatch.pypa.io/latest/plugins/build-hook/custom/
"""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, Final, List, NamedTuple, Union

import httpx
from hatchling.builders.config import BuilderConfig
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from packaging.tags import sys_tags
from typing_extensions import override

RELEASE_VERSION = "1.37.0"
"""Ref: https://github.com/abcfy2/aria2-static-build/releases"""
USE_LIBRESSL = False


_FILE_NAME_TEMPLATE = (
    "aria2-{BUILD}_libressl_static.zip" if USE_LIBRESSL else "aria2-{BUILD}_static.zip"
)

RELEASE_URL = f"https://github.com/abcfy2/aria2-static-build/releases/download/{RELEASE_VERSION}/{_FILE_NAME_TEMPLATE}"
"""需要使用 `.format(BUILD='x86_64-w64-mingw32')` 来生成最终的URL"""


ARIA2_BUILD_ENV_VAR = "CROSS_HOST"
"""Ref: https://github.com/abcfy2/aria2-static-build#build-locally-yourself"""

# keep posix path style
# NOTE: keep the `bin dir` consistent with the one in `src/aria2c/__init__.py`
RELATIVE_BIN_DIR: Final = "src/aria2c/bin/"


class Tag4Build(NamedTuple):
    """用于描述构建平台的tag.

    Attributes:
        aria2_build: aria2c的构建平台, 如x86_64-linux-musl.
            Ref: https://github.com/abcfy2/aria2-static-build
        whl_platform: 最终生成的whl包的平台, 如linux_x86_64.
            Ref: https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/#platform-tag
    """

    aria2_build: str
    whl_platform: str


tag_4_build_enum = (
    Tag4Build("x86_64-linux-musl", "linux_x86_64"),
    Tag4Build("aarch64-linux-musl", "linux_aarch64"),
    Tag4Build("x86_64-w64-mingw32", "win_amd64"),
    Tag4Build("i686-w64-mingw32", "win32"),
)


def _get_tag_4_build_by_env() -> Union[Tag4Build, None]:
    """从环境变量中获取构建平台的tag."""
    aria2_build = os.getenv(ARIA2_BUILD_ENV_VAR)
    if aria2_build is None:
        return None

    for tag in tag_4_build_enum:
        if tag.aria2_build == aria2_build:
            return tag
    else:
        msg = dedent(
            f"""\
            Invalid '{ARIA2_BUILD_ENV_VAR}' env var: {aria2_build}
            Only support: {', '.join(tag.aria2_build for tag in tag_4_build_enum)}
            """
        )
        raise RuntimeError(msg)


def _get_tag_4_build_by_platform() -> Union[Tag4Build, None]:
    """从当前平台获取构建平台的tag."""
    supported_platforms = [tag.platform for tag in sys_tags()]

    for tag in tag_4_build_enum:
        if tag.whl_platform in supported_platforms:
            return tag
    else:
        return None


def get_tag_4_build() -> Tag4Build:
    """获取构建平台的tag."""
    tag = _get_tag_4_build_by_env() or _get_tag_4_build_by_platform()
    if tag is None:
        msg = dedent(
            f"""\
            Can't find tag for build.
            Please set '{ARIA2_BUILD_ENV_VAR}' env var or run this building on supported platform.
                supported platform: {', '.join(tag.whl_platform for tag in tag_4_build_enum)}
            """
        )
        raise RuntimeError(msg)
    return tag


class Aria2cHook(BuildHookInterface[BuilderConfig]):
    """BuildHook.

    Ref:
        https://github.com/pypa/hatch/issues/962
        https://github.com/pact-foundation/pact-python/blob/e9e2ff615078fa245d4e0af4233db89df9b00378/hatch_build.py
    """

    def get_bin_dir(self) -> Path:
        """The directory where the aria2c binary dependencies need to be placed."""
        return Path(self.root) / Path(RELATIVE_BIN_DIR)

    @override
    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        """Download aria2c artifacts and extract them into the bin directory.

        Then, set `tag`, `pure_python` and `artifacts` in `build_data`.
        """
        aria2_tag = get_tag_4_build()
        url = RELEASE_URL.format(BUILD=aria2_tag.aria2_build)
        # tag ref: https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/
        build_data_tag = f"py3-none-{aria2_tag.whl_platform}"

        # https://hatch.pypa.io/latest/plugins/builder/wheel/
        build_data["tag"] = build_data_tag
        build_data["pure_python"] = False
        build_data_artifacts: List[str] = build_data["artifacts"]
        build_data_artifacts.append(
            RELATIVE_BIN_DIR + "aria2c*"
        )  # `aria2c*` 是zip中的aria2c二进制文件，一般为 `aria2c.exe` 或 `aria2c`

        try:
            with tempfile.NamedTemporaryFile() as download_file:
                print("Start download aria2c artifacts...")
                with httpx.stream("GET", url=url, follow_redirects=True) as response:
                    response.raise_for_status()
                    for chunk in response.iter_bytes():
                        download_file.write(chunk)
                download_file.seek(0)
                print("Download aria2c artifacts successfully.")

                abs_bin_dir = self.get_bin_dir()
                abs_bin_dir.mkdir(parents=True, exist_ok=True)

                opened_zipfile = zipfile.ZipFile(download_file)
                # Extract all the files, and set permissions to match the original permissions
                # Ref: https://github.com/python/cpython/pull/32289/
                #      https://github.com/python/cpython/issues/59999
                for member in opened_zipfile.infolist():
                    unzip_file_path = opened_zipfile.extract(member, abs_bin_dir)
                    # Ignore permissions if the archive was created on Windows
                    if member.create_system == 0:
                        continue
                    mode = (member.external_attr >> 16) & 0xFFFF
                    os.chmod(unzip_file_path, mode)

        except Exception as e:
            raise RuntimeError("Failed to download aria2c artifacts.") from e

    @override
    def clean(self, versions: List[str]) -> None:
        """Clean up the entire bin directory.

        Note: Keep the files or directories that will be removed consistent with `.gitignore`
        """
        abs_bin_dir = self.get_bin_dir()
        if abs_bin_dir.exists():
            shutil.rmtree(self.get_bin_dir())
