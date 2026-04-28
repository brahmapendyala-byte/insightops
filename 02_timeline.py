# ============================================================
# InsightOps Intelligence — 02_timeline.py
# Converts D0 raw detections into:
#   D1 — structured appearance events
#   D2 — intelligence summary JSON
# ============================================================

import pandas as pd
import json
import os
from pathlib import Path
from datetime import timedelta

DATA_DIR = "data"
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

GAP_THRESHOLD_SEC = 3   # gap > 3s = new appearance event


def fmt_time(seconds):
    return str(timedelta(seconds=int(seconds)))


def build_timeline(d0_path="data/d0_detections.csv",
                   stills=None):
    """
    Reads D0 CSV, groups detections into D1 events,
    builds D2 intelligence summary JSON.

    Returns d2_summary dict.
    """

    print("=" * 55)
    print("  InsightOps Intelligence — Timeline Builder")
    print("=" * 55)
    print()

    # ── Load D0 ─────────────────────────────────────────────
    if not os.path.exists(d0_path):
        print(f"ERROR: D0 file not found at {d0_path}")
        print("       Run 01_detect.py first.")
        return None

    df = pd.read_csv(d0_path)
    print(f"✓ D0 loaded — {len(df)} raw detections")
    print()

    if df.empty:
        print("ERROR: D0 table is empty. No detections to process.")
        return None

    # ── Build D1 events ──────────────────────────────────────
    print("Building D1 — grouping detections into events...")

    df = df.sort_values("timestamp_sec").reset_index(drop=True)
    events   = []
    event_id = 1
    start_idx = 0

    for i in range(1, len(df)):
        gap = df.loc[i, "timestamp_sec"] - df.loc[i-1, "timestamp_sec"]
        is_last = (i == len(df) - 1)

        if gap > GAP_THRESHOLD_SEC or is_last:
            end_idx = i if not is_last else i + 1
            chunk   = df.iloc[start_idx:end_idx]

            first_ts  = chunk["timestamp_sec"].min()
            last_ts   = chunk["timestamp_sec"].max()
            duration  = last_ts - first_ts
            avg_conf  = chunk["confidence_pct"].mean()
            max_conf  = chunk["confidence_pct"].max()
            row_count = len(chunk)

            # Dominant verdict for this event
            tier_order = ["high", "confirmed", "possible", "none"]
            dominant_tier = "none"
            for t in tier_order:
                if (chunk["tier"] == t).any():
                    dominant_tier = t
                    break

            verdict_map = {
                "high"      : "HIGH MATCH",
                "confirmed" : "CONFIRMED MATCH",
                "possible"  : "POSSIBLE MATCH",
                "none"      : "NO MATCH"
            }
            action_map = {
                "high"      : "Act immediately",
                "confirmed" : "Include in report",
                "possible"  : "Human intervention required",
                "none"      : "Ignore"
            }

            event = {
                "event_id"        : event_id,
                "first_seen_sec"  : round(first_ts, 2),
                "last_seen_sec"   : round(last_ts, 2),
                "first_seen"      : fmt_time(first_ts),
                "last_seen"       : fmt_time(last_ts),
                "duration_sec"    : round(duration, 2),
                "duration_fmt"    : fmt_time(duration),
                "frame_count"     : row_count,
                "avg_confidence"  : round(avg_conf, 1),
                "peak_confidence" : round(max_conf, 1),
                "verdict"         : verdict_map[dominant_tier],
                "action"          : action_map[dominant_tier],
                "tier"            : dominant_tier
            }
            events.append(event)
            event_id += 1
            start_idx = i

    df_d1 = pd.DataFrame(events)
    d1_path = os.path.join(DATA_DIR, "d1_events.json")
    df_d1.to_json(d1_path, orient="records", indent=2)
    print(f"✓ D1 saved — {len(events)} appearance events → {d1_path}")
    print()

    # Print D1 summary
    print("Appearance Events:")
    print("─" * 55)
    for e in events:
        emoji = {"high":"🔴","confirmed":"🟢","possible":"🟡","none":"⚪"}
        print(f"  {emoji.get(e['tier'],'⚪')}  "
              f"Event {e['event_id']}  |  "
              f"{e['first_seen']} → {e['last_seen']}  |  "
              f"Duration: {e['duration_fmt']}  |  "
              f"Peak: {e['peak_confidence']}%  |  "
              f"{e['verdict']}")
    print()

    # ── Build D2 summary ─────────────────────────────────────
    print("Building D2 — intelligence summary...")

    total_visible = df_d1["duration_sec"].sum()
    peak_conf     = df_d1["peak_confidence"].max()
    avg_conf      = df_d1["avg_confidence"].mean()
    first_seen    = fmt_time(df_d1["first_seen_sec"].min())
    last_seen     = fmt_time(df_d1["last_seen_sec"].max())

    # Match result — at least one confirmed or high match
    has_high      = (df_d1["tier"] == "high").any()
    has_confirmed = (df_d1["tier"] == "confirmed").any()
    has_possible  = (df_d1["tier"] == "possible").any()

    if has_high or has_confirmed:
        match_result = "Yes"
        overall_verdict = "HIGH MATCH" if has_high else "CONFIRMED MATCH"
        overall_action  = "Act immediately" if has_high else "Include in report"
    elif has_possible:
        match_result = "Possible"
        overall_verdict = "POSSIBLE MATCH"
        overall_action  = "Human intervention required"
    else:
        match_result = "No"
        overall_verdict = "NO MATCH"
        overall_action  = "No action required"

    # Tier counts
    tier_counts = {
        "high"     : int((df_d1["tier"] == "high").sum()),
        "confirmed": int((df_d1["tier"] == "confirmed").sum()),
        "possible" : int((df_d1["tier"] == "possible").sum()),
    }

    d2 = {
        "match_result"      : match_result,
        "overall_verdict"   : overall_verdict,
        "overall_action"    : overall_action,
        "total_appearances" : len(events),
        "total_visible_sec" : round(total_visible, 2),
        "total_visible_fmt" : fmt_time(total_visible),
        "first_seen"        : first_seen,
        "last_seen"         : last_seen,
        "peak_confidence"   : round(float(peak_conf), 1),
        "avg_confidence"    : round(float(avg_conf), 1),
        "tier_counts"       : tier_counts,
        "timeline"          : events,
        "stills"            : stills or []
    }

    d2_path = os.path.join(DATA_DIR, "d2_summary.json")
    with open(d2_path, "w") as f:
        json.dump(d2, f, indent=2)

    print(f"✓ D2 saved → {d2_path}")
    print()
    print("Intelligence Summary:")
    print("─" * 40)
    print(f"  Match result     : {match_result}")
    print(f"  Overall verdict  : {overall_verdict}")
    print(f"  Action required  : {overall_action}")
    print(f"  Appearances      : {len(events)}")
    print(f"  Total visible    : {fmt_time(total_visible)}")
    print(f"  First seen       : {first_seen}")
    print(f"  Last seen        : {last_seen}")
    print(f"  Peak confidence  : {peak_conf:.1f}%")
    print()
    print(f"  🔴 High matches     : {tier_counts['high']}")
    print(f"  🟢 Confirmed matches: {tier_counts['confirmed']}")
    print(f"  🟡 Possible matches : {tier_counts['possible']}")

    return d2


# ── ENTRY POINT ─────────────────────────────────────────────
if __name__ == "__main__":
    result = build_timeline(
        d0_path="data/d0_detections.csv",
        stills=[]
    )
    if result:
        print("\n" + "="*55)
        print("  ✅  Step 2 complete → run 03_narrate.py next")
        print("="*55)
