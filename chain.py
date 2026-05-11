from openai import OpenAI
from dotenv import load_dotenv
import json

from prompts import (
    SYSTEM_PROMPT,
    stage1_extract,
    stage2_data_model,
    stage3_api_design,
    stage4_production_flags,
    stage5_open_questions,
    stage6_task_breakdown,
    stage7_notion_structure,
    stage8_meeting_note
)
from notion_integration import fetch_notion_context

load_dotenv()
client = OpenAI()

MODEL = "gpt-4o"


def call_ai(prompt, status_label="Thinking..."):
    print(f"\n>>> {status_label}")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    result = response.choices[0].message.content
    print(result)
    return result


def run_chain(brief):
    results = {}

    results["stage1"] = call_ai(stage1_extract(brief), "Stage 1: Extracting domain, users, actions...")
    results["stage2"] = call_ai(stage2_data_model(brief, results["stage1"]), "Stage 2: Designing data model...")
    results["stage3"] = call_ai(stage3_api_design(brief, results["stage2"]), "Stage 3: Designing API endpoints...")
    results["stage4"] = call_ai(stage4_production_flags(brief, results["stage1"]), "Stage 4: Flagging production concerns...")
    results["stage5"] = call_ai(stage5_open_questions(brief, results["stage1"], results["stage4"]), "Stage 5: Identifying open questions...")
    results["stage6"] = call_ai(stage6_task_breakdown(results["stage1"], results["stage2"], results["stage3"]), "Stage 6: Building task breakdown...")

    print("\n>>> Fetching Notion context...")
    notion_context = fetch_notion_context()
    results["notion_context"] = notion_context

    results["stage7"] = call_ai(stage7_notion_structure(results["stage1"], results["stage6"], notion_context), "Stage 7: Structuring for Notion...")
    results["stage8"] = call_ai(stage8_meeting_note(brief, results["stage1"], results["stage4"], results["stage5"]), "Stage 8: Writing meeting note...")

    return results


def parse_notion_payload(raw):
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
            clean = clean.rsplit("```", 1)[0]
        return json.loads(clean)
    except Exception as e:
        print(f"JSON parse error: {e}")
        return None


if __name__ == "__main__":
    brief = """We're building a platform for small restaurant owners to manage their staff 
    schedules and shift swaps."""
    run_chain(brief)