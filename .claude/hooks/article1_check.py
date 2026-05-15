#!/usr/bin/env python3
"""
Article I enforcement hook.

Blocks any Edit or Write to source files that introduces:
  - A bare numeric constant (empirical number)
  - An equation containing numeric operands
  - A comparison threshold
  - A named setting with an opaque value

...without an adjacent comment that cites a domain primitive from Amendment 1.

Receives tool call JSON on stdin. Exits 0 (allow) or 2 (block with message).
"""

import json
import re
import sys

# ─── Patterns that satisfy Article I ──────────────────────────────────────────
# If any of these appear within 3 lines of a flagged value, it is cited.
CITATION_PATTERNS = [
    r'traces to',
    r'amendment\s*1',
    r'primitive\s*\d',
    r'domain primitive',
    r'derived from',
    r'physical derivation',
    r'unit[:\s]',
    r'[A-Z_]{3,}\s*\(',   # e.g. THRESHOLD_DPS( — annotated constant
]

# ─── Source files where Article I applies ─────────────────────────────────────
SOURCE_PATTERNS = [
    r'src/signals\.py$',
    r'src/algorithm\.py$',
    r'\.(c|h|cpp|hpp)$',
]

# ─── Files to skip unconditionally ────────────────────────────────────────────
SKIP_PATTERNS = [
    r'test',
    r'spec',
    r'__init__',
    r'setup\.py$',
    r'conftest',
]


def is_source_file(path: str) -> bool:
    path = path.replace('\\', '/')
    for skip in SKIP_PATTERNS:
        if re.search(skip, path, re.IGNORECASE):
            return False
    return any(re.search(p, path) for p in SOURCE_PATTERNS)


def has_citation(lines: list[str], idx: int) -> bool:
    """True if lines within ±3 of idx contain a primitive citation."""
    window = lines[max(0, idx - 3): idx + 4]
    combined = '\n'.join(window)
    return any(re.search(p, combined, re.IGNORECASE) for p in CITATION_PATTERNS)


def find_violations(content: str) -> list[tuple[int, str, str]]:
    """
    Returns list of (line_number, line_text, matched_snippet) for every
    empirical value that lacks an Article I citation.
    """
    violations = []
    lines = content.split('\n')

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip blank lines
        if not stripped:
            continue

        # Skip pure comment lines
        if re.match(r'^\s*(#|//|\*|/\*)', line):
            continue

        # Skip string-only lines
        if re.match(r"""^\s*['"]""", stripped):
            continue

        # ── Rule 1: bare numeric constant or assignment ─────────────────────
        # Matches: THRESHOLD = 30.0  /  float x = 0.85  /  #define CUTOFF 10
        r1 = re.search(
            r'(?:(?:=|#define\s+\w+)\s*)(\b\d+\.?\d*\b)',
            line
        )

        # ── Rule 2: equation with numeric operand ───────────────────────────
        # Matches: result = a * 0.7 + b * 0.3  /  x / 9.81
        r2 = re.search(
            r'[\w\)]\s*[*/]\s*(\d+\.?\d+)',
            line
        )

        # ── Rule 3: comparison threshold ────────────────────────────────────
        # Matches: if value > 30  /  while count >= 100
        r3 = re.search(
            r'(?:>|<|>=|<=|==)\s*(\d+\.?\d*)\b',
            line
        )

        # ── Rule 4: opaque keyword setting ──────────────────────────────────
        # Matches: cutoff = 10  /  n_steps = 100  /  ODR = 104
        r4 = re.search(
            r'\b(?:cutoff|threshold|limit|rate|freq|odr|gain|scale|alpha|beta|gamma|n_steps|window|timeout)\s*=\s*(\d+\.?\d*)',
            line,
            re.IGNORECASE
        )

        hit = r1 or r2 or r3 or r4
        if hit and not has_citation(lines, i):
            violations.append((i + 1, line.rstrip(), hit.group(0)))

    return violations


def print_violation_report(file_path: str, violations: list[tuple[int, str, str]]) -> None:
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  ARTICLE I VIOLATION — Human intervention required           ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print(f"File: {file_path}")
    print()
    print("The following values have no domain primitive citation (Amendment 1):")
    print()
    for lineno, line_text, match in violations[:6]:
        print(f"  Line {lineno:>4}: {line_text.strip()}")
        print(f"           ↳ '{match}' — empirical value, equation, or opaque setting")
        print()
    if len(violations) > 6:
        print(f"  ... and {len(violations) - 6} more.")
        print()
    print("Required action before this is permitted:")
    print("  Add a comment on or above each flagged line citing the")
    print("  Amendment 1 primitive that justifies the value. Format:")
    print()
    print("  Python:  # Traces to Amendment 1 primitive N: [derivation]")
    print("  C/C++:   /* derived from [primitive name] ([unit]): [formula] */")
    print()
    print("A value without a primitive citation is a guess.")
    print("Guesses are not permitted under Article I — for agents AND engineers.")
    print()


def run_agent_mode() -> None:
    """Called by Claude Code PreToolUse hook — reads tool JSON from stdin."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {})

    if tool_name == 'Write':
        file_path = tool_input.get('file_path', '')
        content = tool_input.get('content', '')
    elif tool_name == 'Edit':
        file_path = tool_input.get('file_path', '')
        content = tool_input.get('new_string', '')
    else:
        sys.exit(0)

    if not file_path or not content or not is_source_file(file_path):
        sys.exit(0)

    violations = find_violations(content)
    if violations:
        print_violation_report(file_path, violations)
        sys.exit(2)
    sys.exit(0)


def run_staged_mode() -> None:
    """Called by git pre-commit hook — checks all staged source files."""
    import subprocess

    result = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
        capture_output=True, text=True
    )
    staged_files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
    source_files = [f for f in staged_files if is_source_file(f)]

    if not source_files:
        sys.exit(0)

    all_violations: list[tuple[str, list[tuple[int, str, str]]]] = []

    for file_path in source_files:
        content_result = subprocess.run(
            ['git', 'show', f':{file_path}'],
            capture_output=True, text=True
        )
        if content_result.returncode != 0:
            continue
        violations = find_violations(content_result.stdout)
        if violations:
            all_violations.append((file_path, violations))

    if all_violations:
        for file_path, violations in all_violations:
            print_violation_report(file_path, violations)
        print("Commit blocked. Fix the violations above, then recommit.")
        sys.exit(1)
    sys.exit(0)


def main():
    if '--staged' in sys.argv:
        run_staged_mode()
    else:
        run_agent_mode()


if __name__ == '__main__':
    main()
