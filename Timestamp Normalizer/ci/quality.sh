#!/usr/bin/env bash
set -euo pipefail

python3 -m compileall -q timestamp_normalizer.py test_timestamp_normalizer.py
ruff check timestamp_normalizer.py test_timestamp_normalizer.py
