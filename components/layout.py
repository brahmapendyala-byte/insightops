import streamlit as st


def setup_page(title: str, icon: str = "🧠") -> None:
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; }
        .metric-card {
            border: 1px solid rgba(49, 51, 63, 0.15);
            border-radius: 16px;
            padding: 18px;
            background: rgba(250, 250, 250, 0.65);
        }
        .small-muted { color: #6b7280; font-size: 0.9rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.title("InsightOps")
        st.caption("Video intelligence MVP")
        st.divider()
        st.page_link("app.py", label="Dashboard", icon="🏠")
        st.page_link("pages/1_New_Investigation.py", label="New Investigation", icon="🎥")
        st.page_link("pages/2_Timeline.py", label="Timeline", icon="🕒")
        st.page_link("pages/3_Matches.py", label="Suspect Matches", icon="🧍")
        st.page_link("pages/4_Narrative.py", label="AI Narrative", icon="📝")
        st.page_link("pages/5_Reports.py", label="Reports", icon="📄")
        st.page_link("pages/6_Settings.py", label="Settings", icon="⚙️")
        st.divider()
        st.caption("Tip: Keep every generated case under output/<case_id>.")


def render_metric_cards(metrics: list[tuple[str, int | str]]) -> None:
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)
