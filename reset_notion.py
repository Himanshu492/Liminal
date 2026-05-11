"""
Reset Notion to original mock state.
Wipes all tasks, projects, companies, and notes — then reseeds.
For local testing only. Do not submit this file.
"""
import os
import requests
from dotenv import load_dotenv
import time

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
TASKS_DB = "35ca3f0633bf801bb8fbebd7c3ed05a8"
PROJECTS_DB = "35ca3f0633bf804ab804e889ce829164"
COMPANIES_DB = "35ca3f0633bf8053ad7edd33c1073a91"
NOTES_DB = "35ca3f0633bf807ab8bbda349cf6d2af"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}


def archive_all_pages(db_id, label):
    print(f"Archiving all pages in {label}...")
    res = requests.post(
        f"https://api.notion.com/v1/databases/{db_id}/query",
        headers=HEADERS,
        json={}
    )
    pages = res.json().get("results", [])
    for page in pages:
        requests.patch(
            f"https://api.notion.com/v1/pages/{page['id']}",
            headers=HEADERS,
            json={"archived": True}
        )
    print(f"  Archived {len(pages)} pages.")


def create_company(name, industry, stage, priority):
    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": COMPANIES_DB},
            "properties": {
                "Name": {"title": [{"text": {"content": name}}]},
                "Industry": {"select": {"name": industry}},
                "Stage": {"select": {"name": stage}},
                "Priority": {"select": {"name": priority}},
                "Status": {"status": {"name": "Active"}}
            }
        }
    )
    return res.json()["id"]


def create_project(name, company_id, priority):
    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": PROJECTS_DB},
            "properties": {
                "Name": {"title": [{"text": {"content": name}}]},
                "Priority": {"select": {"name": priority}},
                "Status": {"status": {"name": "Not started"}},
                "Product": {"relation": [{"id": company_id}]}
            }
        }
    )
    return res.json()["id"]


def create_task(name, project_id, urgency, importance, tags):
    requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": TASKS_DB},
            "properties": {
                "Name": {"title": [{"text": {"content": name}}]},
                "Urgency": {"select": {"name": urgency}},
                "Importance": {"select": {"name": importance}},
                "Status": {"status": {"name": "Not started"}},
                "Project": {"relation": [{"id": project_id}]},
                "Tag": {"multi_select": [{"name": t} for t in tags]}
            }
        }
    )


def create_note(name, company_id, tag, body):
    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": NOTES_DB},
            "properties": {
                "Name": {"title": [{"text": {"content": name}}]},
                "Status": {"select": {"name": "Inbox"}},
                "Tag": {"multi_select": [{"name": tag}]},
                "Company": {"relation": [{"id": company_id}]}
            }
        }
    )
    page_id = res.json()["id"]
    requests.patch(
        f"https://api.notion.com/v1/blocks/{page_id}/children",
        headers=HEADERS,
        json={
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": body}}]
                    }
                }
            ]
        }
    )


def reset_and_seed():
    confirm = input("This wipes ALL data in Tasks, Projects, Companies, Notes. Type 'YES' to continue: ")
    if confirm != "YES":
        print("Aborted.")
        return

    archive_all_pages(TASKS_DB, "Tasks")
    archive_all_pages(PROJECTS_DB, "Projects")
    archive_all_pages(NOTES_DB, "Notes")
    archive_all_pages(PROJECTS_DB, "Projects")
    archive_all_pages(COMPANIES_DB, "Companies")

    print("\nWaiting for Notion to process archives...")
    time.sleep(5)

    print("\nSeeding mock data...")

    # companies
    shiftsync = create_company("ShiftSync", "Restaurant Tech", "MVP", "P1")
    loanbridge = create_company("LoanBridge", "Fintech", "Seed", "P2")
    cargomind = create_company("CargoMind", "Logistics", "MVP", "P3")
    print("Created 3 companies")

    # projects
    p1 = create_project("Core Scheduling Engine", shiftsync, "P1")
    p2 = create_project("Staff & Auth System", shiftsync, "P1")
    p3 = create_project("Notifications & Reminders", shiftsync, "P2")
    p4 = create_project("Loan Application Pipeline", loanbridge, "P1")
    p5 = create_project("Credit Scoring Engine", loanbridge, "P2")
    p6 = create_project("Shipment Tracking API", cargomind, "P1")
    p7 = create_project("Driver Allocation System", cargomind, "P2")
    print("Created 7 projects")

    # tasks (sampling 1-2 per project to match what was in screenshot)
    create_task("Design shifts + shift_assignments schema", p1, "High", "High", ["Database", "Backend"])
    create_task("Build POST /shifts endpoint", p1, "High", "High", ["API", "Backend"])

    create_task("Design users + restaurants schema", p2, "High", "High", ["Database"])
    create_task("Implement OTP login flow", p2, "Low", "Medium", ["Auth", "Backend"])

    create_task("Build shift reminder logic", p3, "Medium", "High", ["Backend", "Notifications"])

    create_task("Design loan application schema", p4, "High", "High", ["Database"])
    create_task("Build application submission API", p4, "High", "High", ["API", "Backend"])

    create_task("Define scoring criteria with founder", p5, "High", "High", ["Research"])

    create_task("Design shipment + waypoint schema", p6, "High", "High", ["Database"])
    create_task("Real-time location update endpoint", p6, "Medium", "High", ["API", "Backend"])

    create_task("Manual override for dispatcher", p7, "Low", "Medium", ["Backend", "Frontend"])
    print("Created 11 tasks")

    # notes
    create_note(
        "Founder call — scheduling pain points",
        shiftsync,
        "Meeting",
        "Biggest pain is not the scheduling itself — it's managers not knowing if staff saw the roster. Confirmation status is must-have for MVP. WhatsApp chaos is the real enemy."
    )
    create_note(
        "Auth approach decision",
        shiftsync,
        "Decision",
        "OTP via phone chosen over email login. Restaurant staff don't check email reliably. SMS cost acceptable at early stage."
    )
    create_note(
        "Credit scoring regulatory risk",
        loanbridge,
        "Research",
        "MAS regulations apply in Singapore. Scoring model needs explainability. Legal review required before any public launch."
    )
    create_note(
        "Driver allocation edge case",
        cargomind,
        "Meeting",
        "Manual dispatcher override is must-have. What happens when zero drivers are available? Auto-retry deferred to v2."
    )
    print("Created 4 notes")

    print("\nReset complete.")


if __name__ == "__main__":
    reset_and_seed()