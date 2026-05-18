#!/usr/bin/env python3
"""Crucible session bootstrap.

Runs once per Claude Code SessionStart (configured in .claude/settings.json).
Verifies the constitutional enforcement stack is wired up correctly, prints a
one-line status, and flags anything the user needs to do manually.

Idempotent: re-firing this every session is intentional. It catches drift
(someone unsetting core.hooksPath, switching python envs, etc.) and surfaces
the fix immediately rather than letting a commit reach CI before failing.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _git(*args: str, cwd: Path) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, cwd=cwd
    )
    return result.returncode, result.stdout.strip()


def _has_module(name: str) -> bool:
    return subprocess.run(
        [sys.executable, "-c", f"import {name}"],
        capture_output=True,
    ).returncode == 0


def main() -> int:
    # SessionStart hooks run from the project directory; resolve it via git.
    rc, repo_root_str = _git("rev-parse", "--show-toplevel", cwd=Path.cwd())
    if rc != 0:
        print("⚠ crucible session-init: not inside a git repository — skipping checks.")
        return 0
    repo_root = Path(repo_root_str)

    issues: list[str] = []
    ok: list[str] = []

    # 1. core.hooksPath must be .githooks
    rc, hp = _git("config", "core.hooksPath", cwd=repo_root)
    if hp != ".githooks":
        print(f"⚠ git core.hooksPath={hp or '(unset)'} — fixing to .githooks")
        _git("config", "core.hooksPath", ".githooks", cwd=repo_root)
        ok.append("core.hooksPath fixed → .githooks")
    else:
        ok.append("core.hooksPath = .githooks")

    # 2. Hook files exist and are executable
    for hook in ("pre-commit", "pre-push"):
        path = repo_root / ".githooks" / hook
        if not path.exists():
            issues.append(f".githooks/{hook} missing")
        elif not path.stat().st_mode & 0o111:
            print(f"⚠ .githooks/{hook} not executable — fixing")
            path.chmod(path.stat().st_mode | 0o755)
            ok.append(f"{hook} made executable")
        else:
            ok.append(f"{hook} present")

    # 3. CI workflow scaffolded
    if (repo_root / ".github" / "workflows" / "constitution-check.yml").exists():
        ok.append("CI workflow scaffolded")
    else:
        issues.append(".github/workflows/constitution-check.yml missing")

    # 4. crucible-core importable from python3 (gates full local enforcement)
    has_core = _has_module("crucible.checks.runner")
    if has_core:
        ok.append("crucible-core importable → full local enforcement active")
    else:
        issues.append(
            "crucible-core not installed in python3 env. "
            "Hooks fall back to Article I only. To enable Corpus + Stage Gate "
            "checks locally: pip install -r requirements.txt"
        )

    # 5. Required governance docs present (the runner reads these)
    for rel in ("docs/governance/amendments.md", "docs/governance/case_law.md"):
        if (repo_root / rel).exists():
            ok.append(f"{rel} present")
        else:
            issues.append(f"{rel} missing — runner will fail")

    # Report
    if not issues:
        print(f"✓ crucible enforcement active ({len(ok)} checks passed)")
    else:
        print(f"✓ {len(ok)} checks passed, ⚠ {len(issues)} item(s) need attention:")
        for i in issues:
            print(f"  - {i}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
