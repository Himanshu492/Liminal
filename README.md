# Venture Brief → Technical Spec

An AI-assisted tool that turns a raw founder brief into a production-aware technical specification — and pushes the output directly into Notion.

Built as a case submission for the Liminal AI / Software Engineering Apprentice role.

---

## What It Does

At a venture studio like Liminal, a junior engineer receives a messy founder brief and is expected to turn it into something buildable. A senior engineer does this instinctively — they know what questions to ask, how to model the data, how to flag production risks, and what to defer. A junior engineer doesn't have that pattern recognition yet.

This tool bridges that gap.

Paste a raw founder brief. The system runs it through an 8-stage AI reasoning chain and produces:

- **Domain & context** — extracted users, core actions, constraints
- **Data model** — every database table the MVP needs, with fields and types
- **API design** — REST endpoints grouped by feature, with request/response shapes
- **Production flags** — scale risks, security concerns, deployment considerations, what to defer
- **Open questions** — blockers that must be answered before writing a line of code
- **Week 1 task breakdown** — must-build vs defer vs do not touch

Everything then gets pushed to a connected Notion workspace: projects, tasks (with urgency/importance scoring), and four structured note pages per brief run.

---

## The Prompt Chain

The core of the system is a multi-stage prompt chain. Each stage does one focused thing and feeds its output into the next.

| Stage | What it does |
|-------|-------------|
| 1 | Extracts domain, users, core actions, constraints |
| 2 | Designs the data model |
| 3 | Designs the REST API |
| 4 | Flags production concerns |
| 5 | Surfaces open questions |
| 6 | Produces week 1 task breakdown |
| 7 | Structures output as JSON for Notion (context-aware) |
| 8 | Writes a clean meeting note summary |

**Why stages instead of one prompt?**
Asking for everything at once produces shallow, inconsistent output. Splitting into stages forces sequential reasoning — the data model informs the API design, which informs the task breakdown. This mirrors how a senior engineer actually thinks through a new project.

**Why context-aware?**
Before pushing to Notion, the system reads existing companies, projects, and tasks from the workspace. The AI is told what already exists so it reuses rather than duplicates. This means the tool works across multiple briefs and multiple ventures without polluting the workspace.

---

## Notion Integration

Each brief run pushes:

- **Tasks** — individual tasks with urgency, importance, tags, and project relation
- **Projects** — grouped under the correct company, with priority (P1/P2/P3)
- **Meeting Note** — a clean 200-300 word summary of the discovery call
- **Technical Spec** — data model + API design in formatted blocks
- **Production Flags** — scale risks, security concerns, deployment considerations
- **Open Questions** — blockers with owners and impact

Existing companies and projects are reused. New ones are created only when needed.

---

## Project Structure

```
liminal-case/
  app.py                  # Streamlit UI
  chain.py                # Multi-stage prompt chain orchestration
  prompts.py              # All prompt templates, versioned and commented
  notion_integration.py   # Notion API integration
  reset_notion.py         # Dev tool — resets Notion to mock baseline (not for submission)
  .env                    # API keys (not committed)
  .env.example            # Key names only
  requirements.txt        # Dependencies
```

---

## Setup

**1. Clone the repo and install dependencies**

```bash
git clone <repo-url>
cd liminal-case
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Set up environment variables**

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```
OPENAI_API_KEY=your_openai_key_here
NOTION_API_KEY=your_notion_key_here
```

**3. Connect Notion**

- Go to [notion.so/my-integrations](https://notion.so/my-integrations) and create an integration
- Share your Tasks, Projects, Companies, and Notes databases with the integration
- The database IDs in `notion_integration.py` point to the demo workspace — update them to your own if needed

**4. Run the app**

```bash
streamlit run app.py
```

---

## Required Notion Schema

| Database | Key Fields |
|----------|-----------|
| Companies | Name, Industry, Stage, Priority, Status |
| Projects | Name, Priority, Status, Product (relation → Companies) |
| Tasks | Name, Urgency, Importance, Status, Project (relation → Projects), Tag |
| Notes | Name, Status, Tag, Company (relation → Companies) |

---

## Requirements

```
openai
streamlit
python-dotenv
requests
```

Install with:

```bash
pip install openai streamlit python-dotenv requests
```

---

## Where It Breaks Down

This tool augments judgment — it does not replace it.

- **Hallucination on vague briefs** — if the brief lacks domain specificity, the data model will be shallow and the open questions will miss the most important unknowns. Every output needs a human pass before it becomes a real spec.
- **No business context** — the tool has no memory of the founder's previous decisions, team constraints, or budget. A senior engineer who knows the founder's history will always produce a better spec.
- **Shallow product judgment** — the tool identifies open questions but cannot weigh them. It does not know which questions block the MVP and which are nice-to-haves.
- **Priority scoring is approximate** — urgency and importance are AI-inferred from the brief. They should be reviewed and adjusted by someone who knows the actual project constraints.
- **Code quality** — if this spec feeds into AI-generated code, errors compound. The human review gate is not optional.

---

## What I Would Build Next

- Feedback loop — let engineers mark tasks as "wrong" and feed corrections back into future runs
- Multi-brief memory — maintain context across multiple founder calls for the same venture
- Spec diffing — show what changed between two versions of the same brief
- Slack integration — post the open questions directly into the team's channel for founder review

---

*Built by Himanshu Sharma — NTU Computer Science, 2027*