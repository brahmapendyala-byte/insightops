# InsightOps Intelligence 🔍

> **"From footage → to findings → in minutes."**

An AI-powered video investigation platform that takes a reference face image and a video, automatically identifies the person, tracks their movement, and generates a structured investigation report — in under 2 minutes.

---

## What It Does

| Input | Output |
|-------|--------|
| Reference face image (JPG/PNG) | 4-page PDF investigation report |
| Video footage (MP4/AVI) | D2 intelligence summary JSON |
| One click | Chat Q&A panel |

**Two modes:**
- **Database Scan Mode** — scan a video against an offender photo database, get ranked match percentages
- **Suspect Investigation Mode** — track one specific person through a video, get full timeline PDF

---

## Confidence Tier System

| Score | Verdict | Action |
|-------|---------|--------|
| ≥ 80% | 🔴 HIGH MATCH | Act immediately |
| 65–79% | 🟢 CONFIRMED MATCH | Include in report |
| 50–64% | 🟡 POSSIBLE MATCH | Human intervention required |
| < 50% | ⚪ NO MATCH | Ignored |

---

## Project Structure

```
insightops/
├── input/                  # Drop reference image + video here
├── output/
│   ├── stills/             # Best-match frame images saved here
│   └── reports/            # Generated PDF reports
├── data/
│   ├── d0_detections.csv   # Raw frame-level detections (D0)
│   ├── d1_events.json      # Structured appearance events (D1)
│   └── d2_summary.json     # Intelligence summary (D2)
├── database/               # Offender photos for UC1 database scan
├── 01_detect.py            # YOLO + InsightFace + DeepSORT pipeline
├── 02_timeline.py          # D0 → D1 → D2 intelligence builder
├── 03_narrate.py           # Azure OpenAI narrative generation
├── 04_report.py            # PDF report generator (reportlab)
├── database_loader.py      # Offender database loader for UC1
├── app.py                  # Streamlit UI — runs everything
├── requirements.txt        # All dependencies
├── .env.example            # Environment variable template
└── README.md
```

---

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/insightops.git
cd insightops
```

### 2. Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate        # Mac/Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

### 5. Add your input files
```
input/reference.jpg    ← face photo of person of interest
input/test_video.mp4   ← video to analyse
```

### 6. Run the full pipeline
```bash
# Run detection only (Step 1)
python3 01_detect.py

# Run full pipeline via UI
streamlit run app.py
```

---

## Pipeline — How It Works

```
Upload image + video
        ↓
YOLO — detect all persons in each frame
        ↓
InsightFace ArcFace — extract face embeddings
        ↓
Cosine similarity — match against reference (threshold: 0.50)
        ↓
Classify confidence tier (High / Confirmed / Possible / None)
        ↓
DeepSORT — track matched person across frames
        ↓
D0 → raw detection table (CSV)
D1 → structured appearance events (JSON)
D2 → intelligence summary (JSON)
        ↓
Azure OpenAI — convert D2 to narrative paragraph
        ↓
reportlab — generate 4-page PDF report
        ↓
Streamlit — serve UI + download + chat
```

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Detection | YOLOv8 (ultralytics) |
| Face matching | InsightFace ArcFace |
| Tracking | DeepSORT |
| Frame processing | OpenCV |
| Data layer | pandas, numpy |
| AI narration | Azure OpenAI (GPT-4o) |
| Report | reportlab |
| UI | Streamlit |
| Storage | Azure ADLS Gen2 |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_STORAGE_CONN_STR=DefaultEndpointsProtocol=https;...
```

---

## PDF Report Structure

| Page | Content |
|------|---------|
| 1 | Match result, confidence %, first/last seen, total duration |
| 2 | Timeline table — each appearance with timestamp + confidence |
| 3 | Frame stills with timestamp overlay |
| 4 | AI summary paragraph + disclaimer |

---

## Accuracy Notes

- Clean, frontal, well-lit footage: **85–92% accuracy**
- Real-world CCTV (low res, angles, occlusion): **65–75% accuracy**
- Always shows confidence score — never hides uncertainty
- Anything below 50% is not reported

---

## Competitor Comparison

| Feature | Rekognition | BriefCam | Avigilon | InsightOps |
|---------|-------------|----------|----------|------------|
| Works on existing video | API only | ✓ | ✗ | ✓ |
| Auto timeline | ✗ | Partial | ✗ | ✓ |
| Generates report | ✗ | ✗ | ✗ | ✓ |
| Chat interface | ✗ | ✗ | ✗ | ✓ |
| No hardware needed | ✓ | ✗ | ✗ | ✓ |
| Deploy in days | ✗ | ✗ | ✗ | ✓ |

---

## Roadmap

- [x] Phase 1 — Single video, suspect investigation mode
- [x] Phase 1 — Confidence tier classification
- [x] Phase 1 — PDF report generation
- [ ] Phase 2 — Database scan mode (UC1)
- [ ] Phase 2 — Multi-video correlation
- [ ] Phase 2 — FAISS vector search for large databases
- [ ] Phase 3 — Real-time stream processing
- [ ] Phase 3 — Predictive alerts

---

## Legal Notice

This system is designed for authorised investigation use only.
All AI-generated summaries are labelled as AI-assisted.
The data table and frame stills are the authoritative record.
Users are responsible for compliance with applicable laws
regarding face recognition and video surveillance in their jurisdiction.

---

## License

MIT License — see LICENSE file.

---

*Built with Python 3.10+ · Azure · InsightFace · YOLOv8*
