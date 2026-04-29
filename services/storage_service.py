from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Any

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
CASES_FILE = DATA_DIR / "cases.json"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def _read_cases() -> list[dict[str, Any]]:
    if not CASES_FILE.exists():
        return []
    return json.loads(CASES_FILE.read_text())


def _write_cases(cases: list[dict[str, Any]]) -> None:
    CASES_FILE.write_text(json.dumps(cases, indent=2))


def create_case(case_id: str, mode: str, video_name: str, suspect_image_name: str | None) -> dict[str, Any]:
    cases = _read_cases()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    case = {
        "case_id": case_id,
        "mode": mode,
        "video": video_name,
        "suspect_image": suspect_image_name or "",
        "status": "Created",
        "created_at": now,
        "updated_at": now,
        "matches": 0,
        "events": 0,
        "report_path": "",
    }
    cases = [c for c in cases if c["case_id"] != case_id]
    cases.insert(0, case)
    _write_cases(cases)
    (OUTPUT_DIR / case_id).mkdir(parents=True, exist_ok=True)
    return case


def update_case(case_id: str, **updates: Any) -> None:
    cases = _read_cases()
    for case in cases:
        if case["case_id"] == case_id:
            case.update(updates)
            case["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    _write_cases(cases)


def get_case(case_id: str) -> dict[str, Any] | None:
    for case in _read_cases():
        if case["case_id"] == case_id:
            return case
    return None


def list_case_ids() -> list[str]:
    return [c["case_id"] for c in _read_cases()]


def list_cases() -> pd.DataFrame:
    cases = _read_cases()
    if not cases:
        return pd.DataFrame(columns=["case_id", "mode", "status", "created_at", "matches", "events"])
    return pd.DataFrame(cases)


def get_case_stats() -> dict[str, int]:
    cases = _read_cases()
    return {
        "total_cases": len(cases),
        "videos_processed": sum(1 for c in cases if c.get("status") in {"Processed", "Report Ready"}),
        "suspect_matches": sum(int(c.get("matches", 0)) for c in cases),
        "reports_generated": sum(1 for c in cases if c.get("report_path")),
    }


def save_uploaded_file(case_id: str, uploaded_file, folder: str) -> Path | None:
    if uploaded_file is None:
        return None
    target_dir = OUTPUT_DIR / case_id / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / uploaded_file.name
    path.write_bytes(uploaded_file.getbuffer())
    return path
