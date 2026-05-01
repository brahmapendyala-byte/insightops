from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Callable

import pandas as pd

from services.storage_service import OUTPUT_DIR, update_case

ProgressFn = Callable[[float, str], None]


def run_pipeline(case_id: str, confidence_threshold: float, progress: ProgressFn | None = None) -> dict:
    """
    MVP pipeline adapter.

    Replace the demo output section with calls to your existing scripts:
      - 01_detect.py
      - 02_timeline.py
      - 03_narrate.py
      - 04_report.py

    Keep this function as the UI boundary so Streamlit does not directly import
    heavy ML models at app startup.
    """
    case_dir = OUTPUT_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    steps = [
        (0.20, "Detecting people and faces"),
        (0.45, "Tracking identities across frames"),
        (0.65, "Building investigation timeline"),
        (0.82, "Generating AI narrative"),
        (1.00, "Preparing report assets"),
    ]

    for pct, label in steps:
        time.sleep(0.3)
        if progress:
            progress(pct, label)

    # Demo data. Replace with actual D0/D1/D2 output files.
    timeline = pd.DataFrame([
        {"timestamp": "00:00:04", "person_id": "P-001", "event": "Person detected near entrance", "confidence": 0.91},
        {"timestamp": "00:00:19", "person_id": "P-001", "event": "Face matched reference image", "confidence": max(confidence_threshold, 0.86)},
        {"timestamp": "00:01:03", "person_id": "P-002", "event": "Unidentified person crossed frame", "confidence": 0.78},
    ])
    matches = pd.DataFrame([
        {"timestamp": "00:00:19", "person_id": "P-001", "similarity": 0.86, "frame": "frame_0019.jpg", "review_status": "Needs Review"},
    ])
    narrative = {
        "case_id": case_id,
        "summary": "A person matching the reference image appears near the entrance and remains visible briefly before leaving the scene.",
        "key_observations": [
            "One high-confidence face match was detected.",
            "One additional unidentified person appears in the timeline.",
            "All AI results should be manually reviewed before final use.",
        ],
    }

    timeline.to_csv(case_dir / "D0_detections.csv", index=False)
    timeline.to_json(case_dir / "D1_events.json", orient="records", indent=2)
    matches.to_csv(case_dir / "matches.csv", index=False)
    (case_dir / "D2_summary.json").write_text(json.dumps(narrative, indent=2))

    update_case(case_id, status="Processed", matches=len(matches), events=len(timeline))
    return {"timeline": timeline, "matches": matches, "narrative": narrative}


def load_timeline(case_id: str) -> pd.DataFrame:
    path = OUTPUT_DIR / case_id / "D1_events.json"
    if path.exists():
        return pd.read_json(path)
    return pd.DataFrame(columns=["timestamp", "person_id", "event", "confidence"])


def load_matches(case_id: str) -> pd.DataFrame:
    path = OUTPUT_DIR / case_id / "matches.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=["timestamp", "person_id", "similarity", "frame", "review_status"])


def load_narrative(case_id: str) -> dict:
    path = OUTPUT_DIR / case_id / "D2_summary.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"summary": "", "key_observations": []}
