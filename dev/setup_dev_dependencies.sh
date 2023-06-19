#!/usr/bin/env bash
# This script will use current path variables. Ensure you are in a virtual environment.
# For Ubuntu: This script will throw an error if run outside a virtual environment.
python -m pip install --upgrade pip &&
pip install poetry &&
poetry install --with dev &&
pre-commit install &&
pre-commit run --all-files
