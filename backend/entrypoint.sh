#!/bin/bash
set -e

cd /backend

# Run the backend server using poetry for now until we fix the venv activation issue
exec poetry run python main.py

# Activate the virtual environment
#source .venv/bin/activate

# Run the backend server using poetry
#exec python main.py
