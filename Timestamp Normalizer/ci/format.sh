#!/usr/bin/env bash
set -euo pipefail

ruff format --check timestamp_normalizer.py test_timestamp_normalizer.py
