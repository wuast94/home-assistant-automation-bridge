from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components" / "wuast_automation_bridge" / "manifest.json"
PYPROJECT = ROOT / "pyproject.toml"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$")


def git(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], cwd=ROOT, text=True).strip()  # noqa: S603, S607


def prepare(version: str) -> None:
    if not SEMVER.fullmatch(version):
        raise SystemExit(f"Invalid semantic version: {version}")
    if git("branch", "--show-current") != "main":
        raise SystemExit("Releases must be prepared from main")
    if git("status", "--porcelain"):
        raise SystemExit("Working tree must be clean before preparing a release")
    tag = f"v{version}"
    if tag in git("tag", "--list", tag).splitlines():
        raise SystemExit(f"Tag already exists: {tag}")

    manifest = json.loads(MANIFEST.read_text())
    if manifest["version"] == version:
        raise SystemExit(f"Version is already {version}")
    manifest["version"] = version
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")

    pyproject = PYPROJECT.read_text()
    updated, replacements = re.subn(
        r'(?m)^(version = ")[^"]+("\s*)$',
        rf"\g<1>{version}\g<2>",
        pyproject,
        count=1,
    )
    if replacements != 1:
        raise SystemExit("Could not update project version")
    PYPROJECT.write_text(updated)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare a bridge release version")
    parser.add_argument("version", help="Semantic version without the v prefix")
    prepare(parser.parse_args().version)
