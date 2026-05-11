import os
import re
import requests
from dotenv import load_dotenv

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

MAX_SEGMENT_LENGTH = 1900

# map common language hints to Notion-supported languages
LANGUAGE_MAP = {
    "python": "python",
    "py": "python",
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    "json": "json",
    "sql": "sql",
    "bash": "shell",
    "sh": "shell",
    "shell": "shell",
    "html": "html",
    "css": "css",
    "java": "java",
    "go": "go",
    "rust": "rust",
    "yaml": "yaml",
    "yml": "yaml",
    "xml": "xml",
    "markdown": "markdown",
    "md": "markdown",
}


def truncate(text):
    return text[:MAX_SEGMENT_LENGTH] if len(text) > MAX_SEGMENT_LENGTH else text


def parse_rich_text(text):
    """Parse inline markdown bold/italic/code into Notion rich_text annotations.
    Triple backticks are handled separately at block level."""
    segments = []
    pattern = re.compile(r'(\*\*(.+?)\*\*|`(.+?)`|\*(.+?)\*|([^*`]+))', re.DOTALL)

    for match in pattern.finditer(text):
        if match.group(2):
            segments.append({
                "type": "text",
                "text": {"content": truncate(match.group(2))},
                "annotations": {"bold": True}
            })
        elif match.group(3):
            # inline code — single backtick
            segments.append({
                "type": "text",
                "text": {"content": truncate(match.group(3))},
                "annotations": {"code": True}
            })
        elif match.group(4):
            segments.append({
                "type": "text",
                "text": {"content": truncate(match.group(4))},
                "annotations": {"italic": True}
            })
        elif match.group(5):
            content = match.group(5)
            while len(content) > MAX_SEGMENT_LENGTH:
                segments.append({
                    "type": "text",
                    "text": {"content": content[:MAX_SEGMENT_LENGTH]}
                })
                content = content[MAX_SEGMENT_LENGTH:]
            if content:
                segments.append({
                    "type": "text",
                    "text": {"content": content}
                })

    return segments if segments else [{"type": "text", "text": {"content": truncate(text)}}]


def make_code_block(code, language="plain text"):
    notion_lang = LANGUAGE_MAP.get(language.lower().strip(), "plain text")
    # truncate code to Notion's 2000 char limit per rich_text
    code_chunks = []
    while len(code) > MAX_SEGMENT_LENGTH:
        code_chunks.append(code[:MAX_SEGMENT_LENGTH])
        code = code[MAX_SEGMENT_LENGTH:]
    if code:
        code_chunks.append(code)

    return {
        "object": "block",
        "type": "code",
        "code": {
            "language": notion_lang,
            "rich_text": [{"type": "text", "text": {"content": c}} for c in code_chunks]
        }
    }


def write_blocks_to_page(page_id, markdown_content):
    blocks = []
    lines = markdown_content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # triple backtick code block
        if stripped.startswith("```"):
            lang = stripped[3:].strip() or "plain text"
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            code = "\n".join(code_lines)
            if code.strip():
                blocks.append(make_code_block(code, lang))
            i += 1
            continue

        if not stripped:
            i += 1
            continue

        if stripped.startswith("### "):
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": parse_rich_text(stripped[4:])}
            })
        elif stripped.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": parse_rich_text(stripped[3:])}
            })
        elif stripped.startswith("# "):
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": parse_rich_text(stripped[2:])}
            })
        elif stripped.startswith("- ") or stripped.startswith("* "):
            clean = stripped.lstrip("-* ").strip()
            if clean:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": parse_rich_text(clean)}
                })
        elif re.match(r'^\d+\.', stripped):
            clean = re.sub(r'^\d+\.\s*', '', stripped).strip()
            if clean:
                blocks.append({
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": parse_rich_text(clean)}
                })
        elif (line.startswith("    ") or line.startswith("\t")) and stripped.startswith("-"):
            clean = stripped.lstrip("-* ").strip()
            if clean:
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": parse_rich_text(clean)}
                })
        else:
            if stripped:
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": parse_rich_text(stripped)}
                })

        i += 1

    # push in chunks of 50
    chunk_size = 50
    for i in range(0, len(blocks), chunk_size):
        chunk = blocks[i:i + chunk_size]
        res = requests.patch(
            "https://api.notion.com/v1/blocks/" + page_id + "/children",
            headers=HEADERS,
            json={"children": chunk}
        )
        result = res.json()
        if result.get("object") == "error":
            print("    Block write error: " + result.get("message", "unknown"))


def query_database(db_id, name):
    res = requests.post(
        "https://api.notion.com/v1/databases/" + db_id + "/query",
        headers=HEADERS,
        json={"filter": {"property": "Name", "title": {"equals": name}}}
    )
    results = res.json().get("results", [])
    return results[0]["id"] if results else None


def fetch_notion_context():
    context = {"companies": [], "projects": [], "tasks": []}

    res = requests.post(
        "https://api.notion.com/v1/databases/" + COMPANIES_DB + "/query",
        headers=HEADERS,
        json={}
    )
    for page in res.json().get("results", []):
        name = page["properties"]["Name"]["title"]
        if name:
            context["companies"].append(name[0]["text"]["content"])

    res = requests.post(
        "https://api.notion.com/v1/databases/" + PROJECTS_DB + "/query",
        headers=HEADERS,
        json={}
    )
    for page in res.json().get("results", []):
        name = page["properties"]["Name"]["title"]
        priority = page["properties"].get("Priority", {}).get("select")
        if name:
            context["projects"].append({
                "name": name[0]["text"]["content"],
                "priority": priority["name"] if priority else "P2"
            })

    res = requests.post(
        "https://api.notion.com/v1/databases/" + TASKS_DB + "/query",
        headers=HEADERS,
        json={}
    )

    for page in res.json().get("results", []):
        name = page["properties"]["Name"]["title"]
        if name:
            context["tasks"].append(name[0]["text"]["content"])

    return context


def get_or_create_company(company_name):
    existing = query_database(COMPANIES_DB, company_name)
    if existing:
        print("  Company exists: " + company_name)
        return existing

    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": COMPANIES_DB},
            "properties": {
                "Name": {"title": [{"text": {"content": company_name}}]},
                "Stage": {"select": {"name": "MVP"}},
                "Status": {"status": {"name": "Active"}},
                "Priority": {"select": {"name": "P1"}}
            }
        }
    )
    
    print("  Created company: " + company_name)
    return res.json()["id"]


def get_or_create_project(project_name, company_id, priority="P2"):
    existing = query_database(PROJECTS_DB, project_name)
    if existing:
        print("    Project exists: " + project_name)
        return existing

    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": PROJECTS_DB},
            "properties": {
                "Name": {"title": [{"text": {"content": project_name}}]},
                "Status": {"status": {"name": "Not started"}},
                "Priority": {"select": {"name": priority}},
                "Product": {"relation": [{"id": company_id}]}
            }
        }
    )
    print("    Created project: " + project_name)
    return res.json()["id"]


def create_task(task, project_id):
    valid_tags = ["API", "Backend", "Database", "Frontend", "Auth", "Notifications", "Devops", "Research"]
    filtered_tags = [t for t in task.get("tags", []) if t in valid_tags]

    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": TASKS_DB},
            "properties": {
                "Name": {"title": [{"text": {"content": task["name"]}}]},
                "Urgency": {"select": {"name": task.get("urgency", "Medium")}},
                "Importance": {"select": {"name": task.get("importance", "Medium")}},
                "Status": {"status": {"name": "Not started"}},
                "Project": {"relation": [{"id": project_id}]},
                "Tag": {"multi_select": [{"name": t} for t in filtered_tags]}
            }
        }
    )
    result = res.json()
    if result.get("object") == "error":
        print("      Task error: " + result.get("message", "unknown"))
    else:
        print("      Task: " + task["name"])


def create_note_page(title, tag, company_id, content):
    valid_tags = ["Meeting", "Decision", "Research"]
    safe_tag = tag if tag in valid_tags else "Meeting"

    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json={
            "parent": {"database_id": NOTES_DB},
            "properties": {
                "Name": {"title": [{"text": {"content": title}}]},
                "Status": {"select": {"name": "Inbox"}},
                "Tag": {"multi_select": [{"name": safe_tag}]},
                "Company": {"relation": [{"id": company_id}]}
            }
        }
    )
    page = res.json()
    if page.get("object") == "error":
        print("    Note error: " + page.get("message", "unknown"))
        return

    write_blocks_to_page(page["id"], content)
    print("    Note created: " + title)


def push_to_notion(spec, notes, company_name):
    print("\nPushing to Notion for: " + company_name)

    company_id = get_or_create_company(company_name)

    for project_data in spec.get("projects", []):
        project_id = get_or_create_project(
            project_data["name"],
            company_id,
            project_data.get("priority", "P2")
        )
        for task in project_data.get("tasks", []):
            create_task(task, project_id)

    for note in notes:
        create_note_page(
            title=note["title"],
            tag=note["tag"],
            company_id=company_id,
            content=note["content"]
        )

    print("\nDone. Check your Notion.")