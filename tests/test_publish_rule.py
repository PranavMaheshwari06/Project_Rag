"""Publish rule: only what a reviewer needs to understand, run or verify the product
is tracked. Build-only material (private notes, handoff files, secrets, hidden tool
folders, repo bundles) stays untracked, so it can never reach the public repo."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PRIVATE_FILES = {"STATUS.md", ".env"}
PRIVATE_DIRS = ("docs/working/", "docs/agents/", "graphify-out/", "data/feedback/")  # feedback: users' notes
PRIVATE_SUFFIXES = (".bundle",)
# Top-level hidden entries a repo of this kind legitimately tracks. Anything else
# hidden (local tool state, editor folders, caches) is build-only by default.
ALLOWED_HIDDEN = {".github", ".gitignore", ".dockerignore", ".env.example", ".python-version"}

def is_private(path: str) -> bool:
    top = path.split("/")[0]
    hidden = top.startswith(".") and top not in ALLOWED_HIDDEN
    return path in PRIVATE_FILES or path.startswith(PRIVATE_DIRS) or path.endswith(PRIVATE_SUFFIXES) or hidden


def test_no_private_file_is_tracked():
    try:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    bad = [p for p in out.splitlines() if is_private(p)]
    assert not bad, f"private build material is tracked, untrack it and add it to .gitignore: {bad}"


def test_the_rule_matches_private_paths_and_only_those():
    for p in ("STATUS.md", ".env", "docs/working/LEARNING.md", "docs/agents/domain.md",
              "graphify-out/graph.json", ".toolstate/settings.json", "backup/all-refs.bundle",
              "data/feedback/feedback.jsonl"):
        assert is_private(p), p
    for p in ("README.md", ".env.example", ".github/workflows/ci.yml", "DECISIONS.md", "docs/project-plan.md", "docs/adr/0001.md",
              "data/verified/kit-m-sc-computer-science.json"):
        assert not is_private(p), p
