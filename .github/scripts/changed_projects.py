"""Emit the top-level utility folders affected by the current GitHub event."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_TOP_LEVEL = {".github", ".git"}
ZERO_SHA = "0" * 40


def git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout


def changed_files() -> list[str]:
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    head_sha = os.environ.get("HEAD_SHA") or "HEAD"

    if event_name == "pull_request":
        base_sha = os.environ.get("BASE_SHA", "")
    else:
        base_sha = os.environ.get("BEFORE_SHA", "")

    if base_sha and base_sha != ZERO_SHA:
        return git("diff", "--name-only", base_sha, head_sha).splitlines()

    # Initial pushes and manual runs do not always provide a usable base SHA.
    # In that case, validate every tracked utility in the current checkout.
    return git("ls-files").splitlines()


def affected_projects(files: list[str]) -> list[str]:
    projects: set[str] = set()
    for file_name in files:
        path = Path(file_name)
        if len(path.parts) < 2:
            continue
        top_level = path.parts[0]
        if top_level in EXCLUDED_TOP_LEVEL or top_level.startswith("."):
            continue
        if (ROOT / top_level).is_dir():
            projects.add(top_level)
    return sorted(projects)


def write_outputs(projects: list[str]) -> None:
    output_file = os.environ.get("GITHUB_OUTPUT")
    if not output_file:
        print(json.dumps(projects))
        return

    with Path(output_file).open("a", encoding="utf-8") as output:
        output.write(f"projects={json.dumps(projects)}\n")
        output.write(f"has_projects={'true' if projects else 'false'}\n")


if __name__ == "__main__":
    write_outputs(affected_projects(changed_files()))
