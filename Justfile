set shell := ["zsh", "-cu"]

uv := "/usr/local/bin/uv"

default: check

sync:
    {{uv}} sync --frozen

format:
    .venv/bin/ruff format custom_components tests scripts
    .venv/bin/ruff check --fix custom_components tests scripts

docs:
    .venv/bin/python scripts/generate_docs.py

docs-check:
    .venv/bin/python scripts/generate_docs.py --check

lint:
    .venv/bin/ruff check custom_components tests scripts
    .venv/bin/ruff format --check custom_components tests scripts

types:
    .venv/bin/pyrefly check custom_components/wuast_automation_bridge

test:
    .venv/bin/pytest

# Auto-fix formatting, regenerate docs, then run every check.
check: sync format docs lint types test docs-check
    git diff --check

# Non-mutating equivalent used to reproduce CI locally.
ci: sync lint types test docs-check
    git diff --check

