SYSTEM_PROMPT = """You are a senior software engineer at a venture studio.
You help turn vague founder briefs into structured technical specifications.
Be specific and practical. No fluff. Output exactly what is asked, nothing more.
Always use proper markdown: ## for section headers, ### for sub-headers, - for bullets.
Always wrap field definitions and code in triple backtick code blocks with the correct language."""


def stage1_extract(brief):
    return f"""Read this founder brief and extract the following. Be specific.

BRIEF:
{brief}

Output exactly this structure. Use bold labels, not headings:

**Domain:** (what industry/space is this)

**Primary Users:** (who uses this, be specific)

**Core Actions:**
- action 1
- action 2
- action 3

**Key Constraints:**
- constraint 1
- constraint 2

**What Is Being Replaced:** (what existing solution/workflow does this replace)"""


def stage2_data_model(brief, stage1_output):
    return f"""You are designing a database for this product.

ORIGINAL BRIEF:
{brief}

EXTRACTED CONTEXT:
{stage1_output}

List every database table needed. For each table use exactly this format:

## TableName
One line explaining what the table stores.

```sql
field_name TYPE -- description
field_name TYPE -- description
```

Only include tables the MVP actually needs. No over-engineering."""


def stage3_api_design(brief, stage2_output):
    return f"""Design the REST API for this product.

DATA MODEL:
{stage2_output}

For each endpoint use exactly this format:

## Feature Name

### METHOD /path
What it does in one sentence.

```json
Request: {{ "field": "type", "field": "type" }}
Response: {{ "field": "type", "field": "type" }}
```

Only include endpoints needed for the core actions. Group by feature."""


def stage4_production_flags(brief, stage1_output):
    return f"""You are a senior engineer reviewing this project before it goes to production.

BRIEF:
{brief}

CONTEXT:
{stage1_output}

Use exactly these markdown section headers and format each point as a numbered list:

## Scale Risks
1. **Risk name:** explanation

## Security Concerns
1. **Concern name:** explanation

## Deployment Considerations
1. **Consideration:** explanation

## What to Defer
1. **Feature:** why it is not needed for MVP"""


def stage5_open_questions(brief, stage1_output, stage4_output):
    return f"""A junior engineer is about to start building this.

BRIEF:
{brief}

CONTEXT:
{stage1_output}

PRODUCTION FLAGS:
{stage4_output}

List the open questions they MUST get answered before writing a single line of code.

Use this format for each question:

### Question title
**The question:** full question here
**Why it blocks development:** explanation
**Who should answer it:** founder / designer / legal / etc"""


def stage6_task_breakdown(stage1_output, stage2_output, stage3_output):
    return f"""Create a week 1 task breakdown for a junior engineer starting this project.

CONTEXT:
{stage1_output}

DATA MODEL:
{stage2_output}

API DESIGN:
{stage3_output}

Use exactly these markdown section headers:

## Must Build — Week 1
- **Task name** — one sentence on why it comes first.

## Defer to Week 2
- **Task name** — why it is not blocking week 1

## Do Not Touch Yet
- **Task name** — why it will waste time now"""


def stage7_notion_structure(stage1_output, stage6_output, notion_context):
    existing_companies = ", ".join(notion_context["companies"]) or "none"
    existing_projects = ", ".join(p["name"] for p in notion_context["projects"]) or "none"
    existing_tasks = ", ".join(notion_context["tasks"][:20]) or "none"

    return f"""Based on this context and task breakdown, produce a JSON object for a Notion workspace.

CONTEXT:
{stage1_output}

TASK BREAKDOWN:
{stage6_output}

EXISTING NOTION DATA (do not duplicate these — reuse names exactly if they match):
Companies: {existing_companies}
Projects: {existing_projects}
Tasks (sample): {existing_tasks}

PRIORITY RULES — follow these strictly:
- P1: must be built in week 1, blocks everything else
- P2: important but not blocking week 1
- P3: future development, deferred features, nice-to-haves
- If a task is labelled "future", "defer", "later", "v2", or "nice to have" — always P3
- Urgency and Importance must reflect actual MVP priority, not aspirational priority

Return ONLY valid JSON, no explanation, no markdown, no backticks. Exactly this structure:
{{
  "projects": [
    {{
      "name": "string — project name",
      "priority": "P1 or P2 or P3",
      "tasks": [
        {{
          "name": "string — specific task name",
          "urgency": "High or Medium or Low",
          "importance": "High or Medium or Low",
          "priority": "P1 or P2 or P3",
          "tags": ["pick from: API, Backend, Database, Frontend, Auth, Notifications, Devops, Research"]
        }}
      ]
    }}
  ]
}}"""


def stage8_meeting_note(brief, stage1_output, stage4_output, stage5_output):
    return f"""You are summarising a founder discovery call into a clean meeting note.

ORIGINAL BRIEF:
{brief}

EXTRACTED CONTEXT:
{stage1_output}

PRODUCTION FLAGS:
{stage4_output}

OPEN QUESTIONS:
{stage5_output}

Produce a JSON object with exactly this structure:
{{
  "title": "string — short descriptive meeting title e.g. 'LoanBridge Discovery Call — Lending Platform MVP'",
  "content": "string — clean readable summary. Include: what the product is, who it is for, core MVP features, key decisions made, what is deferred, main risks, open questions. Write in paragraphs not bullet points. 200-300 words."
}}

Return ONLY valid JSON, no markdown, no backticks."""