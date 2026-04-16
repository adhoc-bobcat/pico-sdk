#!/usr/bin/env python3
#
# Copyright (c) 2026 Raspberry Pi (Trading) Ltd.
#
# SPDX-License-Identifier: BSD-3-Clause
#
# Run buildifier check on all Bazel files.
#

import logging
import os
from pathlib import Path
from typing import Iterable
import subprocess
import sys

from bazel_common import (
    SDK_ROOT,
    run_bazel,
    setup_logging,
    print_framed_string,
    print_to_stderr,
)

_LOG = logging.getLogger(__file__)


def check_buildifier() -> int:
    """Runs the buildifier check on all the Bazel build files.

    This catches ensures consistent formatting and documentation, and catches
    lint errors.
    """

    # Check the standard Bazel build filenames. This does not require listing
    # them all out.
    _LOG.info("Running buildifier check recursively on standard files...")
    args = [
        "run",
        "@buildifier_prebuilt//:buildifier",
        "--",
        "--mode=check",
        "--lint=warn",
        "-r",
        SDK_ROOT,
    ]
    proc = run_bazel(args, check=False, capture_output=True, text=True)
    failed = proc.returncode != 0

    # Find and check *.BUILD files separately as they are not picked up by
    # the recursive check.
    _LOG.info("Scanning for *.BUILD files using git...")
    git_command = ["git", "ls-files", "*.BUILD"]
    result = subprocess.run(
        git_command,
        cwd=SDK_ROOT,
        text=True,
        check=True,
        capture_output=True,
    ).stdout

    # Use absolute paths to ensure this works from any CWD.
    build_files = [
        os.path.abspath(os.path.join(SDK_ROOT, f)) for f in result.splitlines()
    ]

    if build_files:
        _LOG.info(
            f"Found {len(build_files)} *.BUILD files. Running buildifier on them..."
        )
        args = [
            "run",
            "@buildifier_prebuilt//:buildifier",
            "--",
            "--mode=check",
            "--lint=warn",
        ] + build_files
        proc = run_bazel(args, check=False, capture_output=True, text=True)
        failed = failed or proc.returncode != 0

    if failed:
        _LOG.error("ERROR: One or more buildifier checks failed.")
        print_to_stderr("\nTo automatically fix formatting issues in a file, run:")
        print_to_stderr("  bazel run @buildifier_prebuilt//:buildifier -- <file>")
        print_to_stderr("\nTo run the checks manually on a file, run:")
        print_to_stderr(
            "  bazel run @buildifier_prebuilt//:buildifier -- --mode=check --lint=warn <file>\n"
        )
        return 1

    _LOG.info("\x1b[32mBuildifier checks passed.\x1b[0m")
    return 0


if __name__ == "__main__":
    setup_logging()
    sys.exit(check_buildifier())
