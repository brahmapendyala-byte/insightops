# ============================================================
# InsightOps Intelligence — 01_detect.py
# Detects, matches, and tracks a person from a reference
# image through a video file.
# Outputs: D0 CSV, frame stills, match summary
# ============================================================

import cv2
import numpy as np
import pandas as pd
import os
from pathlib import Path
from datetime import timedelta
from ultralytics import YOLO
from insightface.app import FaceAnalysis
from deep_sort_realtime.deepsort_tracker import DeepSort

# ── PATHS ───────────────────────────────────────────────────
INPUT_DIR      = "input"
OUTPUT_STILLS  = "output/stills"
OUTPUT_REPORTS = "output/reports"
DATA_DIR       = "data"

for folder in [INPUT_DIR, OUTPUT_STILLS, OUTPUT_REPORTS, DATA_DIR]:
    Path(folder).mkdir(parents=True, exist_ok=True)

# ── CONFIG ──────────────────────────────────────────────────
MATCH_THRESHOLD = 0.50   # capture everything above 50%
SAMPLE_EVERY_N  = 1      # 1 frame per second

# ── LOAD MODELS ─────────────────────────────────────────────
print("=" * 55)
print("  InsightOps Intelligence — Detection Engine")
print("=" * 55)
print()
print("Loading YOLO model...")
yolo = YOLO("yolov8n.pt")

print("Loading InsightFace model...")
face_app = FaceAnalysis(name="buffalo_l",
                        providers=["CPUExecutionProvider"])
face_app.prepare(ctx_id=0, det_size=(640, 640))

print("Loading DeepSORT tracker...")
tracker = DeepSort(max_age=30)
print("✓ All models loaded\n")


# ── HELPERS ─────────────────────────────────────────────────
def cosine_sim(a, b):
    a = np.array(a).flatten()
    b = np.array(b).flatten()
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom != 0 else 0.0


def fmt_time(seconds):
    return str(timedelta(seconds=int(seconds)))


def classify_confidence(score):
    if score >= 0.80:
        return {"label": "HIGH MATCH",      "action": "Act immediately",
                "tier": "high",             "color": (0, 60, 255),
                "pct": round(score*100, 1)}
    elif score >= 0.65:
        return {"label": "CONFIRMED MATCH", "action": "Include in report",
                "tier": "confirmed",        "color": (0, 200, 100),
                "pct": round(score*100, 1)}
    elif score >= 0.50:
        return {"label": "POSSIBLE MATCH",  "action": "Human intervention required",
                "tier": "possible",         "color": (0, 165, 255),
                "pct": round(score*100, 1)}
    else:
        return {"label": "NO MATCH",        "action": "Ignore",
                "tier": "none",             "color": (128, 128, 128),
                "pct": round(score*100, 1)}


# ── MAIN ────────────────────────────────────────────────────
def run_detection(reference_image_path, video_path):

    print(f"Reference : {reference_image_path}")
    print(f"Video     : {video_path}\n")

    # Step 1 — Reference embedding
    print("Step 1 — Extracting reference face embedding...")
    ref_img = cv2.imread(reference_image_path)
    if ref_img is None:
        print("ERROR: Cannot read reference image. Check path/format.")
        return None
    ref_faces = face_app.get(ref_img)
    if not ref_faces:
        print("ERROR: No face in reference image. Use a clear frontal photo.")
        return None
    ref_embedding = ref_faces[0].embedding
    print(f"✓ Embedding extracted — shape {ref_embedding.shape}\n")

    # Step 2 — Open video
    print("Step 2 — Opening video...")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("ERROR: Cannot open video. Check path/format.")
        return None
    fps          = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration     = total_frames / fps if fps > 0 else 0
    interval     = max(1, int(fps * SAMPLE_EVERY_N))
    print(f"✓ Video opened  |  FPS: {fps:.1f}  |  "
          f"Duration: {fmt_time(duration)}  |  "
          f"Sampling: 1fps\n")

    # Step 3 — Frame loop
    print("Step 3 — Processing frames...")
    print("─" * 55)

    d0_records   = []
    stills       = []
    frame_idx    = 0
    match_count  = 0
    last_still_ts = -30

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % interval != 0:
            frame_idx += 1
            continue

        ts  = frame_idx / fps if fps > 0 else frame_idx
        tss = fmt_time(ts)
        results = yolo(frame, classes=[0], verbose=False)
        dets_for_tracker = []

        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            crop = frame[max(0,y1):min(frame.shape[0],y2),
                         max(0,x1):min(frame.shape[1],x2)]
            if crop.size == 0:
                continue
            try:
                faces = face_app.get(crop)
            except Exception:
                continue
            if not faces:
                continue

            sim     = cosine_sim(ref_embedding, faces[0].embedding)
            verdict = classify_confidence(sim)
            if sim < MATCH_THRESHOLD:
                continue

            match_count += 1
            print(f"  [{tss}]  {verdict['label']:<20}  "
                  f"{sim:.1%}  —  {verdict['action']}")

            dets_for_tracker.append(
                ([x1, y1, x2-x1, y2-y1], sim, "person")
            )

            # Save still every 30 seconds
            if ts - last_still_ts >= 30:
                last_still_ts = ts
                fc = frame.copy()
                cv2.rectangle(fc, (x1,y1), (x2,y2), verdict["color"], 2)
                cv2.putText(fc, f"{verdict['label']} {sim:.0%}",
                            (x1, max(y1-10,20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                            verdict["color"], 2)
                cv2.putText(fc, f"Time: {tss}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (255,255,255), 2)
                cv2.putText(fc, verdict["action"],
                            (10, fc.shape[0]-15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            verdict["color"], 2)
                sname = (f"still_{tss.replace(':','-')}_"
                         f"{verdict['tier']}_{int(sim*100)}pct.jpg")
                spath = os.path.join(OUTPUT_STILLS, sname)
                cv2.imwrite(spath, fc)
                stills.append({"path": spath, "timestamp": tss,
                                "tier": verdict["tier"],
                                "pct": verdict["pct"]})

        # DeepSORT tracking
        tracks = tracker.update_tracks(dets_for_tracker, frame=frame)
        for track in tracks:
            if not track.is_confirmed():
                continue
            ltrb = track.to_ltrb()
            conf = float(track.det_conf) if track.det_conf else 0.0
            v    = classify_confidence(conf)
            d0_records.append({
                "frame_idx"     : frame_idx,
                "timestamp_sec" : round(ts, 2),
                "timestamp_fmt" : tss,
                "track_id"      : track.track_id,
                "cx"            : int((ltrb[0]+ltrb[2])/2),
                "cy"            : int((ltrb[1]+ltrb[3])/2),
                "confidence"    : round(conf, 4),
                "confidence_pct": v["pct"],
                "verdict"       : v["label"],
                "action"        : v["action"],
                "tier"          : v["tier"]
            })
        frame_idx += 1

    cap.release()
    print("─" * 55)
    print(f"\n✓ Processing complete  |  Matches: {match_count}  |  "
          f"Stills: {len(stills)}\n")

    if not d0_records:
        print("⚠  No matches found above 50% threshold.")
        print("   Try: clearer reference photo, or lower MATCH_THRESHOLD")
        return None

    # Step 4 — Save D0
    df = pd.DataFrame(d0_records)
    d0_path = os.path.join(DATA_DIR, "d0_detections.csv")
    df.to_csv(d0_path, index=False)
    print(f"✓ D0 saved → {d0_path}  ({len(df)} rows)\n")

    # Tier summary
    print("Match Summary:")
    print("─" * 40)
    for tier, label, emoji in [
        ("high",      "HIGH MATCH (≥80%)",       "🔴"),
        ("confirmed", "CONFIRMED MATCH (65–79%)", "🟢"),
        ("possible",  "POSSIBLE MATCH (50–64%)",  "🟡"),
    ]:
        n = len(df[df["tier"] == tier])
        if n > 0:
            print(f"  {emoji}  {label:<33}  {n} detections")

    print()
    print(df[["timestamp_fmt","confidence_pct","verdict","action"]].head())

    return {"d0_path": d0_path, "stills": stills, "df_d0": df}


# ── ENTRY POINT ─────────────────────────────────────────────
if __name__ == "__main__":
    REFERENCE_IMAGE = "input/reference.jpg"
    VIDEO_FILE      = "input/test_video.mp4"

    if not os.path.exists(REFERENCE_IMAGE):
        print(f"ERROR: Add reference.jpg to input/ folder")
    elif not os.path.exists(VIDEO_FILE):
        print(f"ERROR: Add test_video.mp4 to input/ folder")
    else:
        result = run_detection(REFERENCE_IMAGE, VIDEO_FILE)
        if result:
            print("\n" + "="*55)
            print("  ✅  Step 1 complete → run 02_timeline.py next")
            print("="*55)