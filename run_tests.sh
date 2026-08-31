#!/bin/bash
set -e

echo "=== Working directory ==="
pwd
ls -la test_cryptid_api.py

echo "=== Python version ==="
python --version

echo "=== Run rebuild ==="
python rebuild_database.py --json-input cryptids_seed.json

echo "=== Run tests ==="
python test_cryptid_api.py
