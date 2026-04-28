# ============================================================
# InsightOps Intelligence — database_loader.py
# Loads offender photos from /database folder and
# pre-computes face embeddings for Use Case 1 (UC1)
# ============================================================

import cv2
import os
import numpy as np
from pathlib import Path


def load_offender_database(db_folder="database", face_app=None):
    """
    Loads all photos from the database folder,
    extracts face embeddings, returns a dict.

    Args:
        db_folder : path to folder containing offender photos
        face_app  : initialised InsightFace FaceAnalysis instance

    Returns:
        dict: { offender_id: {"embedding": np.array,
                               "photo_path": str,
                               "name": str } }
    """

    if face_app is None:
        raise ValueError("face_app (InsightFace) must be provided.")

    db_path = Path(db_folder)
    if not db_path.exists():
        print(f"ERROR: Database folder not found: {db_folder}")
        return {}

    photos = list(db_path.glob("*.jpg")) + \
             list(db_path.glob("*.jpeg")) + \
             list(db_path.glob("*.png"))

    if not photos:
        print(f"⚠  No photos found in {db_folder}/")
        print("   Add offender photos named: offender_001.jpg etc.")
        return {}

    print(f"Loading offender database — {len(photos)} photos...")
    db = {}
    failed = 0

    for photo_path in sorted(photos):
        offender_id = photo_path.stem   # filename without extension
        img = cv2.imread(str(photo_path))

        if img is None:
            print(f"  ⚠  Could not read: {photo_path.name}")
            failed += 1
            continue

        try:
            faces = face_app.get(img)
        except Exception as e:
            print(f"  ⚠  Face detection failed for {photo_path.name}: {e}")
            failed += 1
            continue

        if not faces:
            print(f"  ⚠  No face detected in: {photo_path.name}")
            failed += 1
            continue

        db[offender_id] = {
            "embedding"  : faces[0].embedding,
            "photo_path" : str(photo_path),
            "name"       : offender_id.replace("_", " ").title()
        }
        print(f"  ✓  {offender_id}")

    print(f"\n✓ Database loaded — "
          f"{len(db)} offenders | {failed} failed\n")
    return db


def match_against_database(face_embedding, db, top_n=5):
    """
    Compares a single face embedding against all database entries.
    Returns top N matches sorted by confidence descending.

    Args:
        face_embedding : 512-dim numpy array from InsightFace
        db             : offender database dict from load_offender_database
        top_n          : number of top matches to return

    Returns:
        list of dicts sorted by confidence descending
    """

    if not db:
        return []

    results = []

    for offender_id, entry in db.items():
        db_emb = entry["embedding"]
        a = np.array(face_embedding).flatten()
        b = np.array(db_emb).flatten()
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        sim   = float(np.dot(a, b) / denom) if denom != 0 else 0.0

        # Classify tier
        if sim >= 0.80:
            tier, label = "high",      "HIGH MATCH"
            action       = "Act immediately"
        elif sim >= 0.65:
            tier, label = "confirmed", "CONFIRMED MATCH"
            action       = "Include in report"
        elif sim >= 0.50:
            tier, label = "possible",  "POSSIBLE MATCH"
            action       = "Human intervention required"
        else:
            tier, label = "none",      "NO MATCH"
            action       = "Ignore"

        results.append({
            "offender_id"    : offender_id,
            "name"           : entry["name"],
            "photo_path"     : entry["photo_path"],
            "confidence"     : round(sim, 4),
            "confidence_pct" : round(sim * 100, 1),
            "verdict"        : label,
            "action"         : action,
            "tier"           : tier
        })

    # Sort by confidence descending
    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results[:top_n]
