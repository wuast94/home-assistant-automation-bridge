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

# Automatically prepare, validate, push, and tag the next patch release.
release:
    #!/usr/bin/env zsh
    set -euo pipefail
    version=$(.venv/bin/python scripts/prepare_release.py)
    {{uv}} lock
    just check
    git add custom_components/wuast_automation_bridge/manifest.json pyproject.toml uv.lock
    git commit -m "chore: prepare release v${version}"
    git push origin main
    git push forgejo main
    git tag -a "v${version}" -m "Wuast Automation Bridge ${version}"
    git push origin "v${version}"
    git push forgejo "v${version}"
    echo "Release v${version} triggered"
