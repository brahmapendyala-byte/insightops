from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from services.pipeline_service import load_matches, load_narrative, load_timeline
from services.storage_service import OUTPUT_DIR, update_case


def generate_pdf_report(case_id: str) -> Path:
    case_dir = OUTPUT_DIR / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    report_path = case_dir / f"{case_id}_investigation_report.pdf"

    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("InsightOps Investigation Report", styles["Title"]))
    story.append(Paragraph(f"Case ID: {case_id}", styles["Normal"]))
    story.append(Spacer(1, 14))

    narrative = load_narrative(case_id)
    story.append(Paragraph("AI Narrative", styles["Heading2"]))
    story.append(Paragraph(narrative.get("summary", "No summary available."), styles["BodyText"]))
    story.append(Spacer(1, 12))

    observations = narrative.get("key_observations", [])
    if observations:
        story.append(Paragraph("Key Observations", styles["Heading2"]))
        for item in observations:
            story.append(Paragraph(f"• {item}", styles["BodyText"]))
        story.append(Spacer(1, 12))

    timeline = load_timeline(case_id)
    story.append(Paragraph("Timeline", styles["Heading2"]))
    if not timeline.empty:
        data = [timeline.columns.tolist()] + timeline.astype(str).values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No timeline events available.", styles["BodyText"]))

    story.append(Spacer(1, 12))
    matches = load_matches(case_id)
    story.append(Paragraph("Suspect Matches", styles["Heading2"]))
    if not matches.empty:
        data = [matches.columns.tolist()] + matches.astype(str).values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No suspect matches available.", styles["BodyText"]))

    doc = SimpleDocTemplate(str(report_path), pagesize=LETTER)
    doc.build(story)
    update_case(case_id, status="Report Ready", report_path=str(report_path))
    return report_path
