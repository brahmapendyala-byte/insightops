# ============================================================
# InsightOps Intelligence — 03_narrate.py
# Sends D2 summary JSON to Azure OpenAI.
# Returns a structured 2-3 sentence narrative paragraph.
# LLM only phrases what the data says — no inference.
# ============================================================

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = "data"

SYSTEM_PROMPT = """You are an investigation report writer for a 
security intelligence system.

Your ONLY job is to convert structured JSON data into 
2-3 clear, factual sentences for an investigation report.

Rules you must follow:
- Only describe what the data explicitly states
- Do NOT infer, guess, or add any information not in the JSON
- Do NOT use words like "suspicious", "concerning", or make judgments
- Use plain English — no technical jargon
- Always mention: match result, confidence level, 
  first/last seen times, total visible duration
- If verdict is POSSIBLE MATCH always include: 
  "Human verification is recommended"
- Keep response to 2-3 sentences maximum

This output will appear in a legal investigation document."""


def generate_narrative(d2_path="data/d2_summary.json"):
    """
    Loads D2 summary and generates a narrative paragraph
    using Azure OpenAI.

    Returns narrative string or fallback text if API unavailable.
    """

    print("=" * 55)
    print("  InsightOps Intelligence — Narrative Generator")
    print("=" * 55)
    print()

    # ── Load D2 ─────────────────────────────────────────────
    if not os.path.exists(d2_path):
        print(f"ERROR: D2 file not found at {d2_path}")
        print("       Run 02_timeline.py first.")
        return None

    with open(d2_path, "r") as f:
        d2 = json.load(f)

    print(f"✓ D2 loaded — Match result: {d2['match_result']}")
    print()

    # ── Build minimal prompt data ────────────────────────────
    # Only send what the LLM needs — not the full JSON
    prompt_data = {
        "match_result"      : d2["match_result"],
        "overall_verdict"   : d2["overall_verdict"],
        "overall_action"    : d2["overall_action"],
        "total_appearances" : d2["total_appearances"],
        "total_visible"     : d2["total_visible_fmt"],
        "first_seen"        : d2["first_seen"],
        "last_seen"         : d2["last_seen"],
        "peak_confidence_pct": d2["peak_confidence"],
        "avg_confidence_pct" : d2["avg_confidence"],
        "high_matches"      : d2["tier_counts"]["high"],
        "confirmed_matches" : d2["tier_counts"]["confirmed"],
        "possible_matches"  : d2["tier_counts"]["possible"],
    }

    # ── Check Azure credentials ──────────────────────────────
    api_key    = os.getenv("AZURE_OPENAI_KEY")
    endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    if not api_key or not endpoint:
        print("⚠  Azure OpenAI credentials not found in .env")
        print("   Using fallback narrative template instead.")
        print()
        narrative = _fallback_narrative(d2)
        _save_narrative(narrative, d2_path, d2)
        return narrative

    # ── Call Azure OpenAI ────────────────────────────────────
    try:
        from openai import AzureOpenAI

        print("Calling Azure OpenAI...")

        client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version="2024-02-01"
        )

        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": json.dumps(prompt_data)}
            ],
            max_tokens=200,
            temperature=0.1   # low temperature = consistent output
        )

        narrative = response.choices[0].message.content.strip()
        print(f"✓ Narrative generated ({len(narrative)} chars)")

    except Exception as e:
        print(f"⚠  Azure OpenAI call failed: {e}")
        print("   Using fallback narrative template.")
        narrative = _fallback_narrative(d2)

    # ── Save and return ──────────────────────────────────────
    _save_narrative(narrative, d2_path, d2)
    return narrative


def _fallback_narrative(d2):
    """
    Rule-based narrative template used when Azure OpenAI
    is unavailable. Produces consistent, safe output.
    """
    verdict  = d2["overall_verdict"]
    action   = d2["overall_action"]
    pct      = d2["peak_confidence"]
    first    = d2["first_seen"]
    last     = d2["last_seen"]
    visible  = d2["total_visible_fmt"]
    n        = d2["total_appearances"]

    base = (
        f"The system identified a {verdict.lower()} with a peak "
        f"confidence of {pct}%, first detected at {first} "
        f"and last seen at {last}, "
        f"with a total of {n} appearance event(s) "
        f"spanning {visible} of footage reviewed."
    )

    if d2["tier_counts"]["possible"] > 0 and d2["tier_counts"]["high"] == 0:
        base += " Human verification is recommended before taking action."
    elif d2["tier_counts"]["high"] > 0:
        base += f" Recommended action: {action}."

    return base


def _save_narrative(narrative, d2_path, d2):
    """Append narrative to D2 JSON and save."""
    d2["narrative"] = narrative
    d2["narrative_source"] = (
        "azure_openai"
        if os.getenv("AZURE_OPENAI_KEY") else "fallback_template"
    )
    d2["narrative_disclaimer"] = (
        "AI-assisted narrative. "
        "The data table and frame stills are the authoritative record."
    )

    with open(d2_path, "w") as f:
        json.dump(d2, f, indent=2)

    print()
    print("Generated Narrative:")
    print("─" * 55)
    print(f'  "{narrative}"')
    print()
    print(f"✓ Narrative saved to {d2_path}")


# ── ENTRY POINT ─────────────────────────────────────────────
if __name__ == "__main__":
    narrative = generate_narrative("data/d2_summary.json")
    if narrative:
        print("\n" + "="*55)
        print("  ✅  Step 3 complete → run 04_report.py next")
        print("="*55)
