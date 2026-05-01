# InsightOps Streamlit UI Scaffold

This is a ready-to-copy UI layer for the InsightOps MVP.

## Structure

```text
app.py
pages/
  1_New_Investigation.py
  2_Timeline.py
  3_Matches.py
  4_Narrative.py
  5_Reports.py
  6_Settings.py
components/
  layout.py
services/
  pipeline_service.py
  report_service.py
  storage_service.py
data/
output/
requirements-ui.txt
```

## Run locally

```bash
cd /Users/nethra/projects/insightops
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-ui.txt
streamlit run app.py
```

## How to add to your existing repo

Copy these folders/files into your repository root:

```bash
cp -R app.py pages components services requirements-ui.txt /Users/nethra/projects/insightops/
```

If your repo already has an `app.py`, rename this file first:

```bash
mv app.py streamlit_app.py
streamlit run streamlit_app.py
```

## Where to connect your existing pipeline

Open:

```text
services/pipeline_service.py
```

Replace the demo data in `run_pipeline()` with calls to your current scripts:

```text
01_detect.py
02_timeline.py
03_narrate.py
04_report.py
```

Keep the UI calling only `run_pipeline()` so Streamlit does not load YOLO, InsightFace, or DeepSORT during initial page load.
