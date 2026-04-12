#!/bin/bash
set -e
echo "=== Alethian V2 Test Suite ==="
export PYTHONPATH=$(pwd)/backend

echo "--- Unit Tests ---"
python3 -m pytest backend/tests/unit/ -v --tb=short

echo "--- Integration Tests ---"
python3 -m pytest backend/tests/system/ -v --tb=short

echo "--- Coverage ---"
python3 -m pytest backend/tests/ --cov=backend/app --cov-report=term-missing --cov-fail-under=60
