.PHONY: check format

install:
    #!/usr/bin/env bash
    set -euxo pipefail
    poetry install
    poetry run pre-commit install

check:
	poetry run mypy .
	poetry run vulture
	poetry run ruff .

format:
	poetry run ruff --fix htw

all: check format install