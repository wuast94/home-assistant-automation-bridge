from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "custom_components" / "wuast_automation_bridge" / "manifest.json"
PYPROJECT = ROOT / "pyproject.toml"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def git(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], cwd=ROOT, text=True).strip()  # noqa: S603, S607


def prepare() -> str:
    if git("branch", "--show-current") != "main":
        raise SystemExit("Releases must be prepared from main")
    if git("status", "--porcelain"):
        raise SystemExit("Working tree must be clean before preparing a release")
    manifest = json.loads(MANIFEST.read_text())
    match = SEMVER.fullmatch(manifest["version"])
    if match is None:
        raise SystemExit(f"Current version is not stable semantic version: {manifest['version']}")
    major, minor, patch = (int(part) for part in match.groups())
    version = f"{major}.{minor}.{patch + 1}"
    tag = f"v{version}"
    if tag in git("tag", "--list", tag).splitlines():
        raise SystemExit(f"Tag already exists: {tag}")

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
    return version


if __name__ == "__main__":
    print(prepare())
