# ============================================================
# InsightOps Intelligence — 04_report.py
# Generates a 4-page PDF investigation report from D2 JSON.
# Page 1 — Match summary
# Page 2 — Timeline table
# Page 3 — Frame stills
# Page 4 — AI narrative + disclaimer
# ============================================================

import json
import os
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, Image, PageBreak,
                                 HRFlowable)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

OUTPUT_REPORTS = "output/reports"
DATA_DIR       = "data"
Path(OUTPUT_REPORTS).mkdir(parents=True, exist_ok=True)

# ── COLORS ──────────────────────────────────────────────────
C_BLACK    = colors.HexColor("#0a0a0a")
C_WHITE    = colors.white
C_DARK     = colors.HexColor("#1a1a2e")
C_BLUE     = colors.HexColor("#1d4ed8")
C_GREEN    = colors.HexColor("#166534")
C_AMBER    = colors.HexColor("#92400e")
C_RED      = colors.HexColor("#991b1b")
C_LGRAY    = colors.HexColor("#f8f9fa")
C_BORDER   = colors.HexColor("#e2e8f0")
C_MUTED    = colors.HexColor("#64748b")

TIER_COLORS = {
    "high"      : (colors.HexColor("#fff5f5"), C_RED),
    "confirmed" : (colors.HexColor("#f0fdf4"), C_GREEN),
    "possible"  : (colors.HexColor("#fffbeb"), C_AMBER),
    "none"      : (colors.HexColor("#f8fafc"), C_MUTED),
}


def verdict_color(verdict):
    if "HIGH"      in verdict: return C_RED
    if "CONFIRMED" in verdict: return C_GREEN
    if "POSSIBLE"  in verdict: return C_AMBER
    return C_MUTED


def generate_report(d2_path="data/d2_summary.json"):
    """
    Reads D2 JSON and generates a 4-page PDF report.
    Returns path to generated PDF.
    """

    print("=" * 55)
    print("  InsightOps Intelligence — PDF Report Generator")
    print("=" * 55)
    print()

    if not os.path.exists(d2_path):
        print(f"ERROR: D2 not found at {d2_path}")
        print("       Run 02_timeline.py and 03_narrate.py first.")
        return None

    with open(d2_path) as f:
        d2 = json.load(f)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path  = os.path.join(OUTPUT_REPORTS,
                              f"InsightOps_Report_{timestamp}.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm,   bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Shared styles ────────────────────────────────────────
    def style(name, **kwargs):
        return ParagraphStyle(name, **kwargs)

    s_title  = style("title",  fontSize=22, textColor=C_DARK,
                     fontName="Helvetica-Bold", spaceAfter=4)
    s_sub    = style("sub",    fontSize=11, textColor=C_MUTED,
                     fontName="Helvetica",    spaceAfter=12)
    s_h2     = style("h2",     fontSize=14, textColor=C_DARK,
                     fontName="Helvetica-Bold", spaceBefore=12,
                     spaceAfter=6)
    s_h3     = style("h3",     fontSize=11, textColor=C_DARK,
                     fontName="Helvetica-Bold", spaceAfter=4)
    s_body   = style("body",   fontSize=10, textColor=C_BLACK,
                     fontName="Helvetica",    spaceAfter=6,
                     leading=15)
    s_small  = style("small",  fontSize=8,  textColor=C_MUTED,
                     fontName="Helvetica")
    s_center = style("center", fontSize=10, textColor=C_BLACK,
                     fontName="Helvetica",   alignment=TA_CENTER)
    s_disc   = style("disc",   fontSize=8,  textColor=C_MUTED,
                     fontName="Helvetica-Oblique",
                     borderPadding=8,        leading=13,
                     backColor=C_LGRAY)

    # ════════════════════════════════════════════════════════
    # PAGE 1 — MATCH SUMMARY
    # ════════════════════════════════════════════════════════

    # Header bar
    story.append(Paragraph("INSIGHTOPS INTELLIGENCE", style(
        "kicker", fontSize=9, textColor=C_MUTED,
        fontName="Helvetica", spaceAfter=4,
        letterSpacing=2
    )))
    story.append(Paragraph("Investigation Report", s_title))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y — %H:%M')}  "
        f"| Classification: RESTRICTED",
        s_sub
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=C_BORDER, spaceAfter=16))

    # Match result box
    match   = d2["match_result"]
    verdict = d2["overall_verdict"]
    action  = d2["overall_action"]
    vc      = verdict_color(verdict)

    match_data = [
        ["MATCH RESULT", "VERDICT", "ACTION REQUIRED"],
        [match, verdict, action]
    ]
    match_table = Table(match_data,
                        colWidths=[50*mm, 75*mm, 45*mm])
    match_table.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), C_DARK),
        ("TEXTCOLOR",    (0,0), (-1,0), C_WHITE),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0), 9),
        ("BACKGROUND",   (0,1), (-1,1), C_LGRAY),
        ("FONTNAME",     (0,1), (-1,1), "Helvetica-Bold"),
        ("FONTSIZE",     (0,1), (0,1),  16),
        ("FONTSIZE",     (1,1), (1,1),  11),
        ("TEXTCOLOR",    (0,1), (-1,1), vc),
        ("ALIGN",        (0,0), (-1,-1), "CENTER"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_DARK, C_LGRAY]),
        ("GRID",         (0,0), (-1,-1), 0.5, C_BORDER),
        ("TOPPADDING",   (0,0), (-1,-1), 10),
        ("BOTTOMPADDING",(0,0), (-1,-1), 10),
    ]))
    story.append(match_table)
    story.append(Spacer(1, 12))

    # Key metrics
    story.append(Paragraph("Key Metrics", s_h2))
    metrics = [
        ["Peak Confidence",  f"{d2['peak_confidence']}%",
         "Avg Confidence",   f"{d2['avg_confidence']}%"],
        ["First Seen",       d2["first_seen"],
         "Last Seen",        d2["last_seen"]],
        ["Total Visible",    d2["total_visible_fmt"],
         "Total Appearances",str(d2["total_appearances"])],
        ["High Matches 🔴",  str(d2["tier_counts"]["high"]),
         "Possible Matches 🟡", str(d2["tier_counts"]["possible"])],
    ]
    mt = Table(metrics, colWidths=[42*mm, 38*mm, 42*mm, 38*mm])
    mt.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTNAME",  (0,0), (0,-1),  "Helvetica-Bold"),
        ("FONTNAME",  (2,0), (2,-1),  "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 10),
        ("FONTSIZE",  (1,0), (1,-1),  13),
        ("FONTSIZE",  (3,0), (3,-1),  13),
        ("TEXTCOLOR", (1,0), (1,-1),  C_BLUE),
        ("TEXTCOLOR", (3,0), (3,-1),  C_BLUE),
        ("BACKGROUND",(0,0), (-1,-1), C_LGRAY),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [C_WHITE, C_LGRAY]),
        ("GRID",      (0,0), (-1,-1), 0.5, C_BORDER),
        ("TOPPADDING",(0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
    ]))
    story.append(mt)
    story.append(Spacer(1, 12))

    # Confidence tier legend
    story.append(Paragraph("Confidence Tier Guide", s_h3))
    tiers = [
        ["🔴 HIGH MATCH (≥80%)",      "Act immediately"],
        ["🟢 CONFIRMED MATCH (65-79%)", "Include in report"],
        ["🟡 POSSIBLE MATCH (50-64%)", "Human intervention required"],
        ["⚪ NO MATCH (<50%)",         "Not reported"],
    ]
    tt = Table(tiers, colWidths=[90*mm, 80*mm])
    tt.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,0), (-1,-1),
         [C_WHITE, C_LGRAY, C_WHITE, C_LGRAY]),
        ("GRID",      (0,0), (-1,-1), 0.5, C_BORDER),
        ("TOPPADDING",(0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ]))
    story.append(tt)

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # PAGE 2 — TIMELINE TABLE
    # ════════════════════════════════════════════════════════

    story.append(Paragraph("Appearance Timeline", s_h2))
    story.append(Paragraph(
        f"All detected appearances of the person of interest. "
        f"Total: {d2['total_appearances']} events.",
        s_body
    ))
    story.append(Spacer(1, 8))

    tl_header = ["#", "First Seen", "Last Seen",
                  "Duration", "Peak Conf", "Verdict", "Action"]
    tl_data   = [tl_header]

    for e in d2["timeline"]:
        bg, tc = TIER_COLORS.get(e["tier"],
                                  (C_LGRAY, C_MUTED))
        tl_data.append([
            str(e["event_id"]),
            e["first_seen"],
            e["last_seen"],
            e["duration_fmt"],
            f"{e['peak_confidence']}%",
            e["verdict"],
            e["action"]
        ])

    tl_table = Table(tl_data,
                     colWidths=[10*mm,22*mm,22*mm,
                                20*mm,18*mm,38*mm,42*mm])

    ts_list = [
        ("BACKGROUND",  (0,0), (-1,0), C_DARK),
        ("TEXTCOLOR",   (0,0), (-1,0), C_WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 8),
        ("FONTNAME",    (0,1), (-1,-1), "Helvetica"),
        ("GRID",        (0,0), (-1,-1), 0.5, C_BORDER),
        ("TOPPADDING",  (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("ALIGN",       (5,1), (6,-1), "LEFT"),
    ]
    # Row colors by tier
    for i, e in enumerate(d2["timeline"], start=1):
        bg, tc = TIER_COLORS.get(e["tier"], (C_LGRAY, C_MUTED))
        ts_list.append(("BACKGROUND", (0,i), (-1,i), bg))
        ts_list.append(("TEXTCOLOR",  (5,i), (6,i),  tc))
        ts_list.append(("FONTNAME",   (5,i), (5,i),
                         "Helvetica-Bold"))

    tl_table.setStyle(TableStyle(ts_list))
    story.append(tl_table)

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # PAGE 3 — FRAME STILLS
    # ════════════════════════════════════════════════════════

    story.append(Paragraph("Visual Evidence — Frame Stills", s_h2))
    story.append(Paragraph(
        "Best-confidence frame from each detection event. "
        "Bounding box color indicates confidence tier.",
        s_body
    ))
    story.append(Spacer(1, 8))

    stills = d2.get("stills", [])

    if stills:
        for still in stills:
            path = still.get("path","") if isinstance(still, dict) \
                   else still
            ts   = still.get("timestamp","") if isinstance(still, dict)\
                   else ""
            pct  = still.get("pct","") if isinstance(still, dict) else ""
            tier = still.get("tier","") if isinstance(still, dict) else ""

            if os.path.exists(path):
                try:
                    img = Image(path, width=160*mm, height=90*mm)
                    story.append(img)
                    _, tc = TIER_COLORS.get(tier, (C_LGRAY, C_MUTED))
                    cap = (f"Timestamp: {ts}  |  "
                           f"Confidence: {pct}%  |  "
                           f"Tier: {tier.upper()}")
                    story.append(Paragraph(cap, style(
                        "cap", fontSize=8,
                        textColor=tc,
                        fontName="Helvetica-Bold",
                        alignment=TA_CENTER,
                        spaceAfter=12
                    )))
                except Exception as e:
                    story.append(Paragraph(
                        f"[Still image: {path}]", s_small))
    else:
        story.append(Paragraph(
            "No frame stills were saved during this analysis. "
            "Re-run 01_detect.py to generate stills.",
            s_body
        ))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════
    # PAGE 4 — AI NARRATIVE + DISCLAIMER
    # ════════════════════════════════════════════════════════

    story.append(Paragraph("Investigation Summary", s_h2))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=C_BORDER, spaceAfter=12))

    narrative = d2.get("narrative", "")
    if narrative:
        story.append(Paragraph(f'"{narrative}"', style(
            "quote", fontSize=12,
            textColor=C_DARK,
            fontName="Helvetica-Oblique",
            leading=20,
            leftIndent=10,
            rightIndent=10,
            spaceAfter=16
        )))
    else:
        story.append(Paragraph(
            "Narrative not generated. Run 03_narrate.py.",
            s_body
        ))

    story.append(Spacer(1, 16))

    # Full D2 data recap
    story.append(Paragraph("Full Investigation Data", s_h3))
    recap = [
        ["Field", "Value"],
        ["Match Result",       d2["match_result"]],
        ["Overall Verdict",    d2["overall_verdict"]],
        ["Action Required",    d2["overall_action"]],
        ["Peak Confidence",    f"{d2['peak_confidence']}%"],
        ["Avg Confidence",     f"{d2['avg_confidence']}%"],
        ["First Seen",         d2["first_seen"]],
        ["Last Seen",          d2["last_seen"]],
        ["Total Visible Time", d2["total_visible_fmt"]],
        ["Total Appearances",  str(d2["total_appearances"])],
        ["High Matches",       str(d2["tier_counts"]["high"])],
        ["Confirmed Matches",  str(d2["tier_counts"]["confirmed"])],
        ["Possible Matches",   str(d2["tier_counts"]["possible"])],
        ["Report Generated",   datetime.now().strftime(
                               "%Y-%m-%d %H:%M:%S")],
    ]
    rt = Table(recap, colWidths=[70*mm, 100*mm])
    rt.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), C_DARK),
        ("TEXTCOLOR",   (0,0), (-1,0), C_WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME",    (0,1), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",    (1,1), (1,-1), "Helvetica"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [C_WHITE, C_LGRAY]),
        ("GRID",        (0,0), (-1,-1), 0.5, C_BORDER),
        ("TOPPADDING",  (0,0), (-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(rt)
    story.append(Spacer(1, 20))

    # Disclaimer
    disclaimer = d2.get(
        "narrative_disclaimer",
        "AI-assisted narrative. "
        "The data table and frame stills are the authoritative record."
    )
    story.append(Paragraph(
        f"⚠  DISCLAIMER: {disclaimer} "
        f"This report is intended for authorised investigation use only. "
        f"Confidence scores are mathematical similarity measures and "
        f"do not constitute legal proof of identity. "
        f"All findings must be verified by a qualified investigator "
        f"before any action is taken.",
        style("disc2", fontSize=8, textColor=C_MUTED,
              fontName="Helvetica-Oblique",
              backColor=C_LGRAY,
              borderColor=C_BORDER,
              borderWidth=0.5,
              borderPadding=10,
              leading=13)
    ))

    # ── Build PDF ────────────────────────────────────────────
    doc.build(story)

    print(f"✓ PDF report generated → {pdf_path}")
    return pdf_path


# ── ENTRY POINT ─────────────────────────────────────────────
if __name__ == "__main__":
    path = generate_report("data/d2_summary.json")
    if path:
        print("\n" + "="*55)
        print("  ✅  Step 4 complete → run app.py for full UI")
        print("="*55)
