# ============================================================
# InsightOps Intelligence — app.py
# Streamlit UI — orchestrates the full pipeline
# Two modes: Database Scan | Suspect Investigation
# ============================================================

import streamlit as st
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# ── Page config ─────────────────────────────────────────────
st.set_page_config(
    page_title="InsightOps Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
  .main-header {
    font-size: 2rem; font-weight: 700;
    color: #1e293b; margin-bottom: 0;
  }
  .sub-header {
    font-size: 1rem; color: #64748b; margin-bottom: 2rem;
  }
  .metric-box {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 8px; padding: 1rem; text-align: center;
  }
  .tier-high      { color: #991b1b; font-weight: 600; }
  .tier-confirmed { color: #166534; font-weight: 600; }
  .tier-possible  { color: #92400e; font-weight: 600; }
  .disclaimer {
    font-size: 0.75rem; color: #94a3b8;
    background: #f8fafc; padding: 0.75rem;
    border-radius: 6px; margin-top: 1rem;
  }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────
st.markdown('<p class="main-header">🔍 InsightOps Intelligence</p>',
            unsafe_allow_html=True)
st.markdown('<p class="sub-header">'
            'From footage → to findings → in minutes.'
            '</p>', unsafe_allow_html=True)

st.divider()

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    mode = st.radio(
        "Select Mode",
        ["🔬 Suspect Investigation", "🗄️ Database Scan"],
        help=("Suspect Investigation: track one person through a video.\n"
              "Database Scan: check all faces in video against a database.")
    )

    st.divider()
    st.subheader("Confidence Thresholds")
    threshold = st.slider(
        "Match Threshold", 0.40, 0.90, 0.50, 0.05,
        help="Minimum similarity score to flag as a match."
    )

    st.divider()
    st.subheader("Confidence Tiers")
    st.markdown("🔴 **≥ 80%** — High Match")
    st.markdown("🟢 **65–79%** — Confirmed Match")
    st.markdown("🟡 **50–64%** — Possible Match")
    st.markdown("⚪ **< 50%** — Ignored")

    st.divider()
    st.caption("InsightOps Intelligence v1.0")
    st.caption("For authorised use only.")

# ════════════════════════════════════════════════════════════
# MODE 1 — SUSPECT INVESTIGATION
# ════════════════════════════════════════════════════════════

if "Suspect" in mode:

    st.subheader("🔬 Suspect Investigation Mode")
    st.caption("Upload a reference face image and a video. "
               "The system will find and track the person, "
               "then generate a full investigation PDF.")

    col1, col2 = st.columns(2)

    with col1:
        ref_file = st.file_uploader(
            "Reference Image (face photo)",
            type=["jpg", "jpeg", "png"],
            help="Clear, frontal face photo of person of interest."
        )
        if ref_file:
            st.image(ref_file, caption="Reference image",
                     use_column_width=True)

    with col2:
        vid_file = st.file_uploader(
            "Video File",
            type=["mp4", "avi", "mov"],
            help="Video footage to analyse. Max 5 minutes recommended."
        )
        if vid_file:
            st.video(vid_file)

    st.divider()
    run_btn = st.button("▶  Run Analysis", type="primary",
                        disabled=(not ref_file or not vid_file))

    if run_btn and ref_file and vid_file:
        # Save uploads to temp paths
        with tempfile.TemporaryDirectory() as tmpdir:
            ref_path = os.path.join("input", "reference.jpg")
            vid_path = os.path.join("input", "test_video.mp4")

            Path("input").mkdir(exist_ok=True)
            with open(ref_path, "wb") as f:
                f.write(ref_file.getvalue())
            with open(vid_path, "wb") as f:
                f.write(vid_file.getvalue())

            # ── Run pipeline ─────────────────────────────────
            progress = st.progress(0, text="Starting pipeline...")

            try:
                # Step 1
                progress.progress(10, text="Step 1/4 — Detecting & matching faces...")
                from detect_runner import run_detection_streamlit
                result = run_detection_streamlit(
                    ref_path, vid_path, threshold
                )

                if result is None:
                    st.error("No matches found. Try a clearer reference "
                             "photo or lower the threshold in the sidebar.")
                    st.stop()

                progress.progress(40, text="Step 2/4 — Building timeline...")
                from timeline_runner import build_timeline_streamlit
                d2 = build_timeline_streamlit(result)

                progress.progress(65, text="Step 3/4 — Generating narrative...")
                from narrate_runner import generate_narrative_streamlit
                generate_narrative_streamlit("data/d2_summary.json")

                progress.progress(85, text="Step 4/4 — Building PDF report...")
                from report_runner import generate_report_streamlit
                pdf_path = generate_report_streamlit("data/d2_summary.json")

                progress.progress(100, text="✅ Complete!")

                # ── Show results ──────────────────────────────
                st.success("Analysis complete!")

                with open("data/d2_summary.json") as f:
                    d2_data = json.load(f)

                _show_results(d2_data, pdf_path)

            except ImportError:
                # Direct pipeline (no runner modules yet)
                _run_pipeline_direct(
                    ref_path, vid_path, threshold, progress
                )


# ════════════════════════════════════════════════════════════
# MODE 2 — DATABASE SCAN
# ════════════════════════════════════════════════════════════

else:
    st.subheader("🗄️ Database Scan Mode")
    st.caption("Upload a video. The system will extract all unique faces "
               "and rank them by match percentage against your "
               "offender database.")

    vid_file = st.file_uploader(
        "Video File",
        type=["mp4", "avi", "mov"],
        help="Video to scan against offender database."
    )

    st.info("📁 Place offender photos in the **database/** folder.\n\n"
            "Name format: **offender_001.jpg**, **offender_002.jpg** etc.\n\n"
            f"Currently loaded: "
            f"**{len(list(Path('database').glob('*.jpg')))} photos**")

    if vid_file:
        st.video(vid_file)

    run_btn = st.button("▶  Run Database Scan", type="primary",
                        disabled=not vid_file)

    if run_btn and vid_file:
        st.info("Database Scan Mode — coming in Phase 2. "
                "Use Suspect Investigation Mode for now.")


# ════════════════════════════════════════════════════════════
# HELPER — Show results panel
# ════════════════════════════════════════════════════════════

def _show_results(d2, pdf_path):
    """Display results panel after pipeline runs."""

    st.divider()
    st.subheader("📊 Results")

    # Metric row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Match Result",   d2["match_result"])
    c2.metric("Peak Confidence", f"{d2['peak_confidence']}%")
    c3.metric("First Seen",     d2["first_seen"])
    c4.metric("Last Seen",      d2["last_seen"])
    c5.metric("Total Visible",  d2["total_visible_fmt"])

    st.divider()

    # Tier counts
    t1, t2, t3 = st.columns(3)
    t1.metric("🔴 High Matches",      d2["tier_counts"]["high"])
    t2.metric("🟢 Confirmed Matches", d2["tier_counts"]["confirmed"])
    t3.metric("🟡 Possible Matches",  d2["tier_counts"]["possible"])

    # Verdict
    vc = d2["overall_verdict"]
    if "HIGH" in vc:
        st.error(f"🔴 {vc} — {d2['overall_action']}")
    elif "CONFIRMED" in vc:
        st.success(f"🟢 {vc} — {d2['overall_action']}")
    elif "POSSIBLE" in vc:
        st.warning(f"🟡 {vc} — {d2['overall_action']}")
    else:
        st.info(f"⚪ {vc}")

    st.divider()

    # Timeline table
    if d2.get("timeline"):
        st.subheader("📋 Appearance Timeline")
        import pandas as pd
        tl = pd.DataFrame(d2["timeline"])
        display_cols = ["event_id", "first_seen", "last_seen",
                        "duration_fmt", "peak_confidence",
                        "verdict", "action"]
        cols = [c for c in display_cols if c in tl.columns]
        st.dataframe(tl[cols], use_container_width=True)

    # Chat panel
    st.divider()
    st.subheader("💬 Ask About This Investigation")
    st.caption("Quick answers from the investigation data.")

    q1, q2, q3, q4 = st.columns(4)
    if q1.button("When first seen?"):
        st.info(f"First seen at: **{d2['first_seen']}**")
    if q2.button("Total visible time?"):
        st.info(f"Total visible: **{d2['total_visible_fmt']}**")
    if q3.button("Confidence level?"):
        st.info(f"Peak confidence: **{d2['peak_confidence']}%**  |  "
                f"Average: **{d2['avg_confidence']}%**")
    if q4.button("What action needed?"):
        st.info(f"Recommended action: **{d2['overall_action']}**")

    # Narrative
    if d2.get("narrative"):
        st.divider()
        st.subheader("🤖 AI Summary")
        st.markdown(f'*"{d2["narrative"]}"*')
        st.markdown(
            f'<p class="disclaimer">⚠ {d2.get("narrative_disclaimer","")}'
            f'</p>',
            unsafe_allow_html=True
        )

    # PDF Download
    st.divider()
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📄 Download Investigation Report (PDF)",
                data=f.read(),
                file_name=os.path.basename(pdf_path),
                mime="application/pdf",
                type="primary"
            )

    # JSON Download
    st.download_button(
        label="📦 Download Raw Data (JSON)",
        data=json.dumps(d2, indent=2),
        file_name="d2_intelligence_summary.json",
        mime="application/json"
    )


def _run_pipeline_direct(ref_path, vid_path, threshold, progress):
    """Run pipeline directly when runner modules not present."""
    import sys
    sys.path.insert(0, ".")

    try:
        # Import from our pipeline files
        from importlib import import_module

        progress.progress(15, "Detecting faces...")
        detect = import_module("01_detect".replace("-","_"))

        # Patch threshold
        detect.MATCH_THRESHOLD = threshold

        result = detect.run_detection(ref_path, vid_path)

        if not result:
            st.error("No matches found above threshold.")
            return

        progress.progress(45, "Building timeline...")
        timeline = import_module("02_timeline".replace("-","_"))
        d2 = timeline.build_timeline(
            d0_path=result["d0_path"],
            stills=result["stills"]
        )

        progress.progress(70, "Generating narrative...")
        narrate = import_module("03_narrate".replace("-","_"))
        narrate.generate_narrative("data/d2_summary.json")

        progress.progress(88, "Building PDF...")
        report = import_module("04_report".replace("-","_"))
        pdf_path = report.generate_report("data/d2_summary.json")

        progress.progress(100, "✅ Complete!")
        st.success("Analysis complete!")

        with open("data/d2_summary.json") as f:
            d2_data = json.load(f)
        _show_results(d2_data, pdf_path)

    except Exception as e:
        st.error(f"Pipeline error: {e}")
        st.exception(e)
