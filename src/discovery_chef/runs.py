"""Run folders: every model-backed run writes its artifacts to outputs/runs/<run_id>/."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel

from discovery_chef.paths import EDA_PROFILE_PATH, OUTPUTS_DIR

RUNS_DIR = OUTPUTS_DIR / "runs"

# Code that shapes what the model sees or how its output is judged during a run. Runs are
# only compared with each other when this code and the EDA profile were identical.
_FINGERPRINTED = ("agents", "baseline.py", "citations.py", "context.py", "llm/base.py",
                  "llm/gemini.py", "llm/ollama.py", "orchestrator.py", "retrieval.py")


def code_fingerprint() -> str:
    """Short hash of the prompt-shaping code plus the EDA profile the agents read."""
    package = Path(__file__).parent
    files = []
    for name in _FINGERPRINTED:
        path = package / name
        files += sorted(path.rglob("*.py")) if path.is_dir() else [path]
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(package).as_posix().encode())
        digest.update(path.read_bytes())
    digest.update(EDA_PROFILE_PATH.read_bytes())
    return digest.hexdigest()[:12]


class RunRecorder:
    def __init__(self, mode: str, root: Path | None = None, run_id: str | None = None):
        self.started_at = datetime.now(UTC)
        self.run_id = run_id or f"{self.started_at:%Y%m%d-%H%M%S}-{mode}"
        self.mode = mode
        self.dir = (root or RUNS_DIR) / self.run_id
        self.dir.mkdir(parents=True, exist_ok=False)

    def json(self, relative: str, data) -> Path:
        if isinstance(data, BaseModel):
            data = data.model_dump(mode="json")
        elif is_dataclass(data):
            data = asdict(data)
        path = self.dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def text(self, relative: str, text: str) -> Path:
        path = self.dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
        return path
