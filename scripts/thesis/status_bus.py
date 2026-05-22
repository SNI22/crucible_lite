"""
Tiny file-based status channel shared between the controller and the monitor GUI.

The controller publishes its current stage (and any extra fields) atomically to
a JSON file; the GUI reads it. Decoupled and process-safe — the GUI never needs
to touch the controller's objects, and it works even if the controller isn't
running (read() just returns {}).
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

DEFAULT_STATUS_FILE = Path(tempfile.gettempdir()) / "cloth_thesis_status.json"


def publish(stage: str, status_file: Path = DEFAULT_STATUS_FILE, **fields) -> None:
    """Atomically write the current stage + extra fields to the status file."""
    data = {"stage": stage, "t": time.time(), **fields}
    tmp = Path(f"{status_file}.tmp")
    try:
        tmp.write_text(json.dumps(data))
        os.replace(tmp, status_file)  # atomic on POSIX
    except Exception:
        pass  # status is best-effort; never break motion over it


def read(status_file: Path = DEFAULT_STATUS_FILE) -> dict:
    """Read the latest status; {} if unavailable or stale-unparseable."""
    try:
        return json.loads(Path(status_file).read_text())
    except Exception:
        return {}
