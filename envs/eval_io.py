"""Small helpers for writing scored eval records as JSONL."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Iterable


def write_jsonl(records: Iterable[dict[str, Any]], path: Path) -> None:
    """Write eval records using compact UTF-8 JSONL.

    Writes through a same-directory temp file, then atomically replaces the
    target to avoid leaving a partial JSONL file if the process is interrupted.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            for record in records:
                handle.write(
                    json.dumps(record, ensure_ascii=False, separators=(",", ":"))
                )
                handle.write("\n")
        tmp_path.replace(path)
    except Exception:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
        raise
