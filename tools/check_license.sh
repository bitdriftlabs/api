#!/bin/bash

set -e

python3 ./tools/license_header.py --check "$@"
