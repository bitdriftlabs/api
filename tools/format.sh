#!/bin/bash

set -euo pipefail

buf format -w src/

# Check if git repository is dirty
if [[ -n $(git status --porcelain) ]]; then
  echo "Error: Git repository is dirty. Run tools/format.sh to format files."

  git diff
  exit 1
fi
