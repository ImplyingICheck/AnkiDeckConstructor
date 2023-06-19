# This script will use path variables determined by the current virtual environment (default) or by PATH
#requires -version 5.1
$ErrorActionPreference = "Stop"
python -m pip install --upgrade pip
pip install poetry
poetry install --with dev
pre-commit install
pre-commit run --all-files
