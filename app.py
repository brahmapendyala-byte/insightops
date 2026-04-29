# ============================================================
# InsightOps Intelligence — app.py
# Single-file Streamlit UI that orchestrates the full pipeline
# Modes: Suspect Investigation | Database Scan
# ============================================================

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

# Optional dependency used only when timeline data is displayed.
try:
    import pandas as pd
except ImportError:  # Keeps the app from failing at startup if pandas is missing.
    pd = None


# ── Constants ───────────────────────────────────────────────
APP_NAME = "InsightOps Intelligence"
APP_VERSION = "v1.0"
INPUT_DIR = Path("input")
DATA_DIR = Path("data")
DATABASE_DIR = Path("database")
REPORTS_DIR = Path("reports")
REFERENCE_IMAGE_PATH = INPUT_DIR / "reference.jpg"
VIDEO_PATH = INPUT_DIR / "test_video.mp4"
D2_SUMMARY_PATH = DATA_DIR / "d2_summary.json"


# ── Page config ─────────────────────────────────────────────
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Styling ─────────────────────────────────────────────────
def apply_styles() -> None:
    st.markdown(
        """
        <style>
          .main-header {
            font-size: 2.2rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.1rem;
          }
          .sub-header {
            font-size: 1rem;
            color: #64748b;
            margin-bottom: 1.5rem;
          }
          .soft-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 1rem 1.15rem;
            margin-bottom: 1rem;
          }
          .section-title {
            font-size: 1.15rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 0.4rem;
          }
          .muted {
            color: #64748b;
            font-size: 0.92rem;
          }
          .disclaimer {
            font-size: 0.78rem;
            color: #64748b;
            background: #f8fafc;
            border-left: 4px solid #cbd5e1;
            padding: 0.75rem;
            border-radius: 8px;
            margin-top: 1rem;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── General helpers ─────────────────────────────────────────
def ensure_project_dirs() -> None:
    for folder in [INPUT_DIR, DATA_DIR, DATABASE_DIR, REPORTS_DIR]:
        folder.mkdir(exist_ok=True)


def safe_get(data: Dict[str, Any], key: str, default: Any = "—") -> Any:
    value = data.get(key, default)
    return default if value is None or value == "" else value


def save_uploaded_file(uploaded_file, target_path: Path) -> Path:
    target_path.parent.mkdir(exist_ok=True)
    with open(target_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    return target_path


def load_module_from_file(module_name: str, file_name: str):
    """Load files like 01_detect.py that cannot be imported with normal syntax."""
    file_path = Path(file_name)
    if not file_path.exists():
        raise FileNotFoundError(f"Required pipeline file not found: {file_name}")

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {file_name}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def get_database_photo_count() -> int:
    extensions = ["*.jpg", "*.jpeg", "*.png"]
    return sum(len(list(DATABASE_DIR.glob(ext))) for ext in extensions)


def render_header() -> None:
    st.markdown(f'<p class="main-header">🔍 {APP_NAME}</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">From footage → to findings → to report-ready intelligence.</p>',
        unsafe_allow_html=True,
    )


def render_dashboard() -> None:
    st.subheader("📊 Investigation Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reports", len(list(REPORTS_DIR.glob("*.pdf"))))
    c2.metric("D2 Summaries", len(list(DATA_DIR.glob("*summary*.json"))))
    c3.metric("Database Photos", get_database_photo_count())
    c4.metric("Mode", "Ready")

    st.markdown(
        """
        <div class="soft-card">
          <div class="section-title">Recommended workflow</div>
          <div class="muted">
            1. Upload a clear reference face image.<br/>
            2. Upload the investigation video.<br/>
            3. Adjust the match threshold if needed.<br/>
            4. Run analysis, review matches, then download PDF/JSON evidence output.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> tuple[str, float, bool]:
    with st.sidebar:
        st.header("⚙️ Configuration")

        mode = st.radio(
            "Select Mode",
            ["🔬 Suspect Investigation", "🗄️ Database Scan"],
            help=(
                "Suspect Investigation tracks one person through a video.\n"
                "Database Scan will compare all detected faces against stored images."
            ),
        )

        st.divider()
        st.subheader("Confidence Threshold")
        threshold = st.slider(
            "Match Threshold",
            min_value=0.40,
            max_value=0.90,
            value=0.50,
            step=0.05,
            help="Minimum similarity score required to flag a match.",
        )

        strict_review = st.checkbox(
            "Require manual review note",
            value=True,
            help="Adds a clear reminder that AI findings should be manually verified.",
        )

        st.divider()
        st.subheader("Confidence Tiers")
        st.markdown("🔴 **≥ 80%** — High Match")
        st.markdown("🟢 **65–79%** — Confirmed Match")
        st.markdown("🟡 **50–64%** — Possible Match")
        st.markdown("⚪ **< 50%** — Ignored")

        st.divider()
        st.caption(f"{APP_NAME} {APP_VERSION}")
        st.caption("For authorized use only.")

    return mode, threshold, strict_review


# ════════════════════════════════════════════════════════════
# Results rendering
# ════════════════════════════════════════════════════════════
def show_results(d2: Dict[str, Any], pdf_path: Optional[str]) -> None:
    """Display results panel after pipeline runs."""
    st.divider()
    st.subheader("📊 Analysis Results")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Match Result", safe_get(d2, "match_result"))
    c2.metric("Peak Confidence", f"{safe_get(d2, 'peak_confidence', 0)}%")
    c3.metric("First Seen", safe_get(d2, "first_seen"))
    c4.metric("Last Seen", safe_get(d2, "last_seen"))
    c5.metric("Total Visible", safe_get(d2, "total_visible_fmt"))

    tier_counts = d2.get("tier_counts", {}) or {}
    t1, t2, t3 = st.columns(3)
    t1.metric("🔴 High Matches", tier_counts.get("high", 0))
    t2.metric("🟢 Confirmed Matches", tier_counts.get("confirmed", 0))
    t3.metric("🟡 Possible Matches", tier_counts.get("possible", 0))

    verdict = str(safe_get(d2, "overall_verdict", "UNKNOWN"))
    action = safe_get(d2, "overall_action", "Manual review recommended")
    if "HIGH" in verdict.upper():
        st.error(f"🔴 {verdict} — {action}")
    elif "CONFIRMED" in verdict.upper():
        st.success(f"🟢 {verdict} — {action}")
    elif "POSSIBLE" in verdict.upper():
        st.warning(f"🟡 {verdict} — {action}")
    else:
        st.info(f"⚪ {verdict} — {action}")

    tabs = st.tabs(["📋 Timeline", "🤖 Narrative", "💬 Quick Q&A", "📦 Downloads"])

    with tabs[0]:
        timeline = d2.get("timeline") or []
        if timeline:
            if pd is None:
                st.json(timeline)
                st.warning("Install pandas for a table view: pip install pandas")
            else:
                tl = pd.DataFrame(timeline)
                display_cols = [
                    "event_id",
                    "first_seen",
                    "last_seen",
                    "duration_fmt",
                    "peak_confidence",
                    "verdict",
                    "action",
                ]
                cols = [c for c in display_cols if c in tl.columns]
                st.dataframe(tl[cols] if cols else tl, use_container_width=True)
        else:
            st.info("No timeline entries were found in the D2 summary.")

    with tabs[1]:
        narrative = d2.get("narrative")
        if narrative:
            st.markdown(narrative)
        else:
            st.info("No AI narrative found yet.")

        disclaimer = d2.get("narrative_disclaimer") or (
            "AI-generated findings must be reviewed by an authorized human reviewer before action is taken."
        )
        st.markdown(f'<p class="disclaimer">⚠️ {disclaimer}</p>', unsafe_allow_html=True)

    with tabs[2]:
        q1, q2, q3, q4 = st.columns(4)
        if q1.button("When first seen?"):
            st.info(f"First seen at: **{safe_get(d2, 'first_seen')}**")
        if q2.button("Total visible time?"):
            st.info(f"Total visible: **{safe_get(d2, 'total_visible_fmt')}**")
        if q3.button("Confidence level?"):
            st.info(
                f"Peak confidence: **{safe_get(d2, 'peak_confidence', 0)}%** | "
                f"Average: **{safe_get(d2, 'avg_confidence', 0)}%**"
            )
        if q4.button("Action needed?"):
            st.info(f"Recommended action: **{action}**")

    with tabs[3]:
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📄 Download Investigation Report (PDF)",
                    data=f.read(),
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf",
                    type="primary",
                )
        else:
            st.warning("PDF report was not found or has not been generated yet.")

        st.download_button(
            label="📦 Download Raw Data (JSON)",
            data=json.dumps(d2, indent=2),
            file_name="d2_intelligence_summary.json",
            mime="application/json",
        )


def run_pipeline_with_runners(ref_path: Path, vid_path: Path, threshold: float, progress) -> tuple[Dict[str, Any], Optional[str]]:
    """Run using optional runner modules, if the repo has them."""
    progress.progress(10, text="Step 1/4 — Detecting and matching faces...")
    from detect_runner import run_detection_streamlit

    result = run_detection_streamlit(str(ref_path), str(vid_path), threshold)
    if result is None:
        raise ValueError("No matches found. Try a clearer reference photo or lower the threshold.")

    progress.progress(40, text="Step 2/4 — Building timeline...")
    from timeline_runner import build_timeline_streamlit

    build_timeline_streamlit(result)

    progress.progress(65, text="Step 3/4 — Generating narrative...")
    from narrate_runner import generate_narrative_streamlit

    generate_narrative_streamlit(str(D2_SUMMARY_PATH))

    progress.progress(85, text="Step 4/4 — Building PDF report...")
    from report_runner import generate_report_streamlit

    pdf_path = generate_report_streamlit(str(D2_SUMMARY_PATH))

    with open(D2_SUMMARY_PATH, "r", encoding="utf-8") as f:
        d2_data = json.load(f)

    return d2_data, pdf_path


def run_pipeline_direct(ref_path: Path, vid_path: Path, threshold: float, progress) -> tuple[Dict[str, Any], Optional[str]]:
    """Run pipeline directly when runner modules are not present."""
    progress.progress(15, text="Detecting faces...")
    detect = load_module_from_file("detect_pipeline", "01_detect.py")

    if hasattr(detect, "MATCH_THRESHOLD"):
        detect.MATCH_THRESHOLD = threshold

    if not hasattr(detect, "run_detection"):
        raise AttributeError("01_detect.py must expose run_detection(ref_path, vid_path).")

    result = detect.run_detection(str(ref_path), str(vid_path))
    if not result:
        raise ValueError("No matches found above threshold.")

    progress.progress(45, text="Building timeline...")
    timeline = load_module_from_file("timeline_pipeline", "02_timeline.py")
    if not hasattr(timeline, "build_timeline"):
        raise AttributeError("02_timeline.py must expose build_timeline(...).")

    timeline.build_timeline(
        d0_path=result.get("d0_path"),
        stills=result.get("stills"),
    )

    progress.progress(70, text="Generating narrative...")
    narrate = load_module_from_file("narrate_pipeline", "03_narrate.py")
    if hasattr(narrate, "generate_narrative"):
        narrate.generate_narrative(str(D2_SUMMARY_PATH))

    progress.progress(88, text="Building PDF...")
    report = load_module_from_file("report_pipeline", "04_report.py")
    pdf_path = None
    if hasattr(report, "generate_report"):
        pdf_path = report.generate_report(str(D2_SUMMARY_PATH))

    with open(D2_SUMMARY_PATH, "r", encoding="utf-8") as f:
        d2_data = json.load(f)

    return d2_data, pdf_path


def run_full_pipeline(ref_path: Path, vid_path: Path, threshold: float, progress) -> tuple[Dict[str, Any], Optional[str]]:
    """Try runner modules first; fall back to direct numbered pipeline files."""
    try:
        return run_pipeline_with_runners(ref_path, vid_path, threshold, progress)
    except ImportError:
        return run_pipeline_direct(ref_path, vid_path, threshold, progress)


# ════════════════════════════════════════════════════════════
# Mode screens
# ════════════════════════════════════════════════════════════
def render_suspect_investigation(threshold: float, strict_review: bool) -> None:
    st.subheader("🔬 Suspect Investigation Mode")
    st.caption(
        "Upload a reference face image and a video. The system will find and track the person, "
        "then generate timeline data, an AI summary, and a PDF report."
    )

    col1, col2 = st.columns(2)
    with col1:
        ref_file = st.file_uploader(
            "Reference Image (face photo)",
            type=["jpg", "jpeg", "png"],
            help="Use a clear, frontal face photo of the person of interest.",
        )
        if ref_file:
            st.image(ref_file, caption="Reference image", use_container_width=True)

    with col2:
        vid_file = st.file_uploader(
            "Video File",
            type=["mp4", "avi", "mov"],
            help="Video footage to analyze. Shorter videos are faster for MVP testing.",
        )
        if vid_file:
            st.video(vid_file)

    review_note = ""
    if strict_review:
        review_note = st.text_area(
            "Manual Review Note",
            placeholder="Example: Reviewed by investigator before report export.",
            help="This note is for workflow discipline. It is not currently written into the PDF unless your report module uses it.",
        )

    st.divider()
    disabled = not ref_file or not vid_file or (strict_review and not review_note.strip())
    run_btn = st.button("▶ Run Analysis", type="primary", disabled=disabled)

    if disabled:
        st.caption("Upload both files and complete the review note to enable analysis.")

    if run_btn and ref_file and vid_file:
        save_uploaded_file(ref_file, REFERENCE_IMAGE_PATH)
        save_uploaded_file(vid_file, VIDEO_PATH)

        progress = st.progress(0, text="Starting pipeline...")
        try:
            d2_data, pdf_path = run_full_pipeline(REFERENCE_IMAGE_PATH, VIDEO_PATH, threshold, progress)
            progress.progress(100, text="✅ Complete!")
            st.success("Analysis complete.")
            show_results(d2_data, pdf_path)
        except Exception as e:
            st.error(f"Pipeline error: {e}")
            st.exception(e)


def render_database_scan() -> None:
    st.subheader("🗄️ Database Scan Mode")
    st.caption(
        "Upload a video. In a future phase, the system will extract unique faces and rank them "
        "against the offender image database."
    )

    vid_file = st.file_uploader(
        "Video File",
        type=["mp4", "avi", "mov"],
        help="Video to scan against offender database.",
    )

    st.info(
        "📁 Place offender photos in the **database/** folder.\n\n"
        "Recommended name format: **offender_001.jpg**, **offender_002.jpg**, etc.\n\n"
        f"Currently loaded: **{get_database_photo_count()} photos**"
    )

    if vid_file:
        st.video(vid_file)

    run_btn = st.button("▶ Run Database Scan", type="primary", disabled=not vid_file)
    if run_btn:
        st.warning("Database Scan Mode is not wired yet. Use Suspect Investigation Mode for now.")


# ════════════════════════════════════════════════════════════
# Main app
# ════════════════════════════════════════════════════════════
def main() -> None:
    ensure_project_dirs()
    apply_styles()
    render_header()

    mode, threshold, strict_review = render_sidebar()

    overview_tab, investigation_tab = st.tabs(["🏠 Dashboard", "🚀 Run Investigation"])
    with overview_tab:
        render_dashboard()

    with investigation_tab:
        if "Suspect" in mode:
            render_suspect_investigation(threshold, strict_review)
        else:
            render_database_scan()


if __name__ == "__main__":
    main()
