# api - bitdrift's client/server API definitions
# Copyright Bitdrift, Inc. All rights reserved.
#
# Use of this source code and APIs are governed by a source available license that can be found in
# the LICENSE file or at:
# https://polyformproject.org/licenses/strict/1.0.0

import argparse
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys


STRICT_URL = 'https://polyformproject.org/licenses/strict/1.0.0'
STRICT_LICENSE_SHA256 = '90f9e6b7d79f381706abd79e5302039ca09856922a2cdc9bc91087fd1535581e'

HEADER = """
// api - bitdrift's client/server API definitions
// Copyright Bitdrift, Inc. All rights reserved.
//
// Use of this source code and APIs are governed by a source available license that can be found in
// the LICENSE file or at:
// https://polyformproject.org/licenses/strict/1.0.0
""".lstrip()

EXCLUDED_DIRS = {'.git', 'protoc-gen-validate', 'thirdparty'}
EXTENSIONS = {'.proto', '.fbs'}


def is_excluded(path: Path) -> bool:
    return bool(path.parts) and path.parts[0] in EXCLUDED_DIRS


def check_file(path: Path, check: bool) -> bool:
    if is_excluded(path) or path.suffix not in EXTENSIONS:
        return True

    print(f'Checking {path}')
    original = path.read_text()
    banner = HEADER.splitlines(keepends=True)[0]
    for match in re.finditer(re.escape(banner), original):
        block = original[match.start():].partition('\n\n')[0]
        if not original.startswith(HEADER, match.start()) and re.search(
            r'^//[^\n]*licens', block, flags=re.MULTILINE | re.IGNORECASE,
        ):
            print(f'Unrecognized license header: {path}', file=sys.stderr)
            return False
    content = original
    while content.startswith(HEADER):
        content = content[len(HEADER):].lstrip('\n')

    expected = HEADER + '\n' + content.lstrip('\n')
    if original != expected:
        if check:
            print(f'Missing or incorrect license header: {path}', file=sys.stderr)
            return False
        path.write_text(expected)
    return True


def iterate_over_files():
    files = subprocess.check_output(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'])
    for name in sorted(set(os.fsdecode(files).split('\0')) - {''}):
        path = Path(name)
        if path.is_file() and not is_excluded(path):
            yield path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Check without modifying files')
    parser.add_argument('files', nargs='*')
    args = parser.parse_args()
    try:
        if hashlib.sha256(Path('LICENSE').read_bytes()).hexdigest() != STRICT_LICENSE_SHA256:
            raise RuntimeError('LICENSE must contain PolyForm Strict License 1.0.0')
        paths = (Path(os.path.relpath(path)) for path in args.files) if args.files else iterate_over_files()
        valid = True
        for path in paths:
            valid = check_file(path, args.check) and valid
        return 0 if valid else 1
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
