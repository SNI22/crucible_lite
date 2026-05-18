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

GOVERNANCE_STAGING_DIR_REL = Path("docs/.adoption/source_governance")
GOVERNANCE_FILES_TO_STAGE = [
    "docs/governance/amendments.md",
    "docs/governance/case_law.md",
]
GOVERNANCE_DIRS_TO_STAGE = [
    "docs/governance/bills",
]


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


def _governance_has_user_content(project_dir: Path) -> bool:
    """Detect whether existing governance files hold real project content
    (a ratified amendment, recorded case law, drafted bills) rather than
    being the unmodified template."""
    amendments = project_dir / "docs/governance/amendments.md"
    if amendments.exists():
        try:
            text = amendments.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = ""
        if "Status: RATIFIED" in text:
            return True
    case_law = project_dir / "docs/governance/case_law.md"
    if case_law.exists():
        try:
            text = case_law.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = ""
        # Template line: "*(No precedents recorded yet...". Real entries: "### Case ".
        if "### Case " in text:
            return True
    bills = project_dir / "docs/governance/bills"
    if bills.exists() and bills.is_dir():
        # Any file in bills/ other than a README counts as user content.
        for p in bills.iterdir():
            if p.is_file() and p.name.lower() != "readme.md":
                return True
    return False


def _stage_governance(project_dir: Path) -> bool:
    """Preserve user governance content before the template copy overwrites it.

    Moves amendments.md, case_law.md, and bills/ into
    docs/.adoption/source_governance/ when those files contain real content.
    Mirrors _stage_adoption(): same pattern, same staging location, same
    intent — never silently destroy ratified governance on `crucible init`.

    Returns True if any content was staged.
    """
    if not _governance_has_user_content(project_dir):
        return False

    staging_dir = project_dir / GOVERNANCE_STAGING_DIR_REL
    staging_dir.mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    for rel in GOVERNANCE_FILES_TO_STAGE:
        src = project_dir / rel
        if src.exists():
            dest = staging_dir / Path(rel).name
            if dest.exists():
                dest.unlink()
            shutil.move(str(src), str(dest))
            moved.append(rel)

    for rel in GOVERNANCE_DIRS_TO_STAGE:
        src = project_dir / rel
        if src.exists() and src.is_dir():
            dest = staging_dir / Path(rel).name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(src), str(dest))
            moved.append(rel)

    today = dt.date.today().isoformat()
    readme = staging_dir / "README.md"
    readme.write_text(
        "# Staged governance content\n\n"
        f"`crucible init` ran in this directory on {today} and found ratified\n"
        "governance content. To avoid silently destroying it, the following\n"
        "files were moved here BEFORE the framework templates were installed:\n\n"
        + "".join(f"- `{rel}`\n" for rel in moved)
        + "\n"
        "## Why this happened\n\n"
        "Templates ship a fresh, unratified `amendments.md` and an empty\n"
        "`case_law.md`. Overwriting your ratified content would destroy the\n"
        "constitutional record of every Hearing, Bill, and Amendment to date.\n"
        "Re-running `crucible init` (intentionally or by accident) preserves\n"
        "rather than clobbers.\n\n"
        "## What to do next\n\n"
        "Merge your preserved content back into the freshly-installed templates:\n\n"
        "  1. `diff source_governance/amendments.md ../../governance/amendments.md`\n"
        "  2. Copy Amendment 1 (and any subsequent project amendments) into the\n"
        "     new file. Keep the template's framework amendments unless you have\n"
        "     a specific reason to diverge.\n"
        "  3. Move your case_law entries and bills back. The template versions\n"
        "     are empty placeholders.\n\n"
        "Once the merge is done, delete this directory:\n\n"
        "  `rm -rf docs/.adoption/source_governance/`\n",
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
    # If governance files already exist with ratified content, preserve them too —
    # never silently overwrite Amendment 1, case law, or bills.
    governance_staged = _stage_governance(project_dir)

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
        if governance_staged:
            commit_msg += " (prior governance preserved at docs/.adoption/source_governance/)"
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
    if governance_staged:
        print()
        print("  *** GOVERNANCE PRESERVED ***")
        print(f"  Existing ratified governance was moved to {GOVERNANCE_STAGING_DIR_REL}/")
        print(f"  before the template overwrite. Merge it back into the freshly")
        print(f"  installed docs/governance/ files, then delete the staging dir.")
        print(f"  See {GOVERNANCE_STAGING_DIR_REL}/README.md for the merge checklist.")
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


def cmd_check(args: argparse.Namespace) -> int:
    """Run the constitutional checks using crucible-core's own python.

    Exists so git hooks and CI can invoke the checks without resolving
    'which python3 has crucible-core installed'. Whatever interpreter
    runs the `crucible` CLI is the one that runs the checks.
    """
    from crucible.checks.runner import main as runner_main
    runner_argv: list[str] = []
    if args.base_ref:
        runner_argv.extend(["--base-ref", args.base_ref])
    if args.pre_commit:
        runner_argv.append("--pre-commit")
    return runner_main(runner_argv)


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

    p_check = sub.add_parser(
        "check",
        help="Run the constitutional check stack (Article I + Corpus + Stage Gate).",
    )
    p_check.add_argument(
        "--base-ref",
        default=None,
        help="Git ref to diff against (e.g. origin/main). Default: HEAD~1.",
    )
    p_check.add_argument(
        "--pre-commit",
        action="store_true",
        help="Pre-commit mode: staged files only, warnings do not block.",
    )
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
