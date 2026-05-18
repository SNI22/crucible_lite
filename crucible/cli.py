"""Crucible CLI — bootstrap a project workspace from the framework templates."""
from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path


TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

CLAUDE_MD = "CLAUDE.md"
ADOPTION_DIR_REL = Path("docs/.adoption")
ADOPTION_SOURCE_NAME = "source_CLAUDE.md"
ADOPTION_PENDING_NAME = "PENDING.md"


def harness_memory_path(project_path: Path) -> Path:
    encoded = str(project_path.resolve()).replace("/", "-")
    return Path.home() / ".claude" / "projects" / encoded


def _template_relpaths(templates_dir: Path) -> list[Path]:
    return [p.relative_to(templates_dir) for p in templates_dir.rglob("*") if p.is_file()]


def _stage_adoption(project_dir: Path) -> bool:
    """If CLAUDE.md exists, move it into docs/.adoption/ and write a sentinel.

    Returns True if an adoption was staged (i.e. there was an existing CLAUDE.md).
    """
    existing = project_dir / CLAUDE_MD
    if not existing.exists():
        return False

    adoption_dir = project_dir / ADOPTION_DIR_REL
    adoption_dir.mkdir(parents=True, exist_ok=True)
    source_dest = adoption_dir / ADOPTION_SOURCE_NAME
    shutil.move(str(existing), str(source_dest))

    today = dt.date.today().isoformat()
    pending = adoption_dir / ADOPTION_PENDING_NAME
    pending.write_text(
        "# Crucible adoption PENDING\n\n"
        f"`crucible init` ran in this directory on {today} and found an existing\n"
        "`CLAUDE.md` that pre-dates Crucible adoption. The original content was\n"
        f"preserved verbatim at `{ADOPTION_DIR_REL}/{ADOPTION_SOURCE_NAME}` and\n"
        "the Crucible CLAUDE.md template was installed in its place.\n\n"
        "## What to do next\n\n"
        "In your first Claude Code session in this directory, invoke the\n"
        "`claude-md-adopter` agent. It will:\n\n"
        f"  1. Read `{ADOPTION_DIR_REL}/{ADOPTION_SOURCE_NAME}`.\n"
        "  2. Classify each section by destination (device_context.md,\n"
        "     toolchain_config.md, agent files, REPO_GUIDE.md, or CLAUDE.md tail).\n"
        "  3. Verify every proposal passes the Article I git pre-commit hook.\n"
        "  4. Produce a per-destination edit proposal table for human review.\n\n"
        "Apply the proposals you accept, then remove this sentinel file and\n"
        f"`{ADOPTION_DIR_REL}/{ADOPTION_SOURCE_NAME}` once the adoption is complete.\n",
        encoding="utf-8",
    )
    return True


def cmd_init(args: argparse.Namespace) -> int:
    project_dir = Path.cwd().resolve()
    project_name = project_dir.name

    if not TEMPLATES_DIR.exists():
        print(f"error: templates directory not found at {TEMPLATES_DIR}", file=sys.stderr)
        return 2

    # If CLAUDE.md already exists, stage it for adoption BEFORE checking conflicts.
    adoption_staged = _stage_adoption(project_dir)

    template_files = _template_relpaths(TEMPLATES_DIR)
    conflicts = [rel for rel in template_files if (project_dir / rel).exists()]
    if conflicts and not args.force:
        print(f"error: the following files already exist in {project_dir}:", file=sys.stderr)
        for c in conflicts:
            print(f"  {c}", file=sys.stderr)
        print(file=sys.stderr)
        print("Re-run with --force to overwrite, or move/remove the conflicting files first.", file=sys.stderr)
        if adoption_staged:
            print(
                f"(Your original CLAUDE.md is safe at {ADOPTION_DIR_REL}/{ADOPTION_SOURCE_NAME}.)",
                file=sys.stderr,
            )
        return 1

    for rel in template_files:
        dest = project_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(TEMPLATES_DIR / rel, dest)

    memory_dir = project_dir / "docs" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    memory_index = memory_dir / "MEMORY.md"
    if not memory_index.exists():
        memory_index.write_text("", encoding="utf-8")

    harness_dir = harness_memory_path(project_dir)
    harness_dir.mkdir(parents=True, exist_ok=True)
    harness_symlink = harness_dir / "memory"
    if harness_symlink.exists() or harness_symlink.is_symlink():
        harness_symlink.unlink()
    harness_symlink.symlink_to(memory_dir)

    crucible_registry = Path.home() / "crucible" / project_name
    crucible_registry.parent.mkdir(parents=True, exist_ok=True)
    if crucible_registry.is_symlink():
        if crucible_registry.resolve() != project_dir:
            crucible_registry.unlink()
            crucible_registry.symlink_to(project_dir)
    elif crucible_registry.exists():
        print(
            f"warning: {crucible_registry} already exists and is not a symlink; leaving it alone.",
            file=sys.stderr,
        )
    else:
        crucible_registry.symlink_to(project_dir)

    if not args.no_git:
        is_repo = (project_dir / ".git").exists()
        if not is_repo:
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=project_dir, check=True)
        if (project_dir / ".githooks" / "pre-commit").exists():
            subprocess.run(
                ["git", "config", "core.hooksPath", ".githooks"],
                cwd=project_dir,
                check=True,
            )
        subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)
        commit_msg = (
            f"Initialize {project_name} from crucible-core templates"
            if not is_repo
            else f"Add Crucible governance scaffold to {project_name}"
        )
        if adoption_staged:
            commit_msg += " (adoption pending — invoke claude-md-adopter)"
        subprocess.run(
            ["git", "commit", "-q", "-m", commit_msg],
            cwd=project_dir,
            check=False,
        )

    print(f"crucible initialized in {project_dir}")
    print(f"  templates copied from {TEMPLATES_DIR}")
    print(f"  memory: {memory_dir} (symlinked from {harness_symlink})")
    print(f"  registry: {crucible_registry} -> {project_dir}")
    if not args.no_git:
        print(f"  git hooks: core.hooksPath = .githooks")
    if adoption_staged:
        print()
        print("  *** ADOPTION PENDING ***")
        print(f"  Your original CLAUDE.md was moved to {ADOPTION_DIR_REL}/{ADOPTION_SOURCE_NAME}.")
        print(f"  See {ADOPTION_DIR_REL}/{ADOPTION_PENDING_NAME} for next-step instructions.")
        print(f"  First Claude Code task here: invoke the claude-md-adopter agent.")
    print()

    if args.no_claude:
        print("Next: launch Claude Code here when ready.")
        print(f"  cd {project_dir} && claude")
        return 0

    claude_bin = shutil.which("claude")
    if not claude_bin:
        print("claude command not found on PATH.")
        print(f"Install Claude Code, then run: cd {project_dir} && claude")
        return 0

    print("Launching Claude Code...")
    os.execv(claude_bin, ["claude"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="crucible",
        description="Crucible Constitutional Governance Framework CLI.",
    )
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser(
        "init",
        help="Initialize Crucible in the current directory and launch Claude Code.",
    )
    p_init.add_argument(
        "--no-git",
        action="store_true",
        help="Skip git init / staging / commit and hook activation",
    )
    p_init.add_argument(
        "--no-claude",
        action="store_true",
        help="Do not launch Claude Code at the end; just print the next-step hint",
    )
    p_init.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files that conflict with the templates. "
             "An existing CLAUDE.md is always preserved separately under "
             "docs/.adoption/source_CLAUDE.md regardless of this flag.",
    )
    p_init.set_defaults(func=cmd_init)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
