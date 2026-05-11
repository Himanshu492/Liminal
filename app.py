import streamlit as st
from chain import call_ai, parse_notion_payload
from notion_integration import push_to_notion, fetch_notion_context
from prompts import (
    stage1_extract,
    stage2_data_model,
    stage3_api_design,
    stage4_production_flags,
    stage5_open_questions,
    stage6_task_breakdown,
    stage7_notion_structure,
    stage8_meeting_note
)

st.set_page_config(page_title="Venture Brief → Technical Spec", layout="wide")

# ── session state init ──────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = None
if "notion_payload" not in st.session_state:
    st.session_state.notion_payload = None
if "note_payload" not in st.session_state:
    st.session_state.note_payload = None
if "company_name" not in st.session_state:
    st.session_state.company_name = ""
if "brief" not in st.session_state:
    st.session_state.brief = ""

# ── header ──────────────────────────────────────────────────────────────────
st.markdown("## Venture Brief → Technical Spec")
st.caption(
    "Paste a raw founder brief. The system extracts context, designs a data model and API, "
    "flags production risks, surfaces open questions, and pushes structured output to Notion."
)
st.divider()

# ── input ───────────────────────────────────────────────────────────────────
col_brief, col_company = st.columns([4, 1])

with col_brief:
    brief = st.text_area(
        "Founder Brief",
        height=160,
        value=st.session_state.brief,
        placeholder="Paste the raw brief here. Messy is fine — that's the point.",
        label_visibility="collapsed"
    )
    st.session_state.brief = brief

with col_company:
    st.markdown("**Company Name**")
    company_name = st.text_input(
        "company_name",
        value=st.session_state.company_name,
        placeholder="e.g. LoanBridge",
        label_visibility="collapsed",
        help="Exact name. If it already exists in Notion it will be reused."
    )
    generate = st.button(
        "Generate Spec",
        disabled=not brief or not company_name,
        use_container_width=True
    )

# ── generation ──────────────────────────────────────────────────────────────
if generate:
    results = {}
    progress = st.progress(0, text="Starting...")

    with st.spinner("Stage 1 — Extracting domain, users, actions..."):
        results["stage1"] = call_ai(stage1_extract(brief))
    progress.progress(12, text="Stage 1 done")

    with st.spinner("Stage 2 — Designing data model..."):
        results["stage2"] = call_ai(stage2_data_model(brief, results["stage1"]))
    progress.progress(25, text="Stage 2 done")

    with st.spinner("Stage 3 — Designing API endpoints..."):
        results["stage3"] = call_ai(stage3_api_design(brief, results["stage2"]))
    progress.progress(37, text="Stage 3 done")

    with st.spinner("Stage 4 — Flagging production concerns..."):
        results["stage4"] = call_ai(stage4_production_flags(brief, results["stage1"]))
    progress.progress(50, text="Stage 4 done")

    with st.spinner("Stage 5 — Identifying open questions..."):
        results["stage5"] = call_ai(stage5_open_questions(brief, results["stage1"], results["stage4"]))
    progress.progress(62, text="Stage 5 done")

    with st.spinner("Stage 6 — Building task breakdown..."):
        results["stage6"] = call_ai(stage6_task_breakdown(results["stage1"], results["stage2"], results["stage3"]))
    progress.progress(75, text="Stage 6 done")

    with st.spinner("Fetching Notion context..."):
        notion_context = fetch_notion_context()
    progress.progress(80, text="Notion context fetched")

    with st.spinner("Stage 7 — Structuring tasks for Notion..."):
        results["stage7"] = call_ai(stage7_notion_structure(results["stage1"], results["stage6"], notion_context))
    progress.progress(90, text="Stage 7 done")

    with st.spinner("Stage 8 — Writing meeting note..."):
        results["stage8"] = call_ai(stage8_meeting_note(brief, results["stage1"], results["stage4"], results["stage5"]))
    progress.progress(100, text="Done")

    st.session_state.results = results
    st.session_state.company_name = company_name
    st.session_state.notion_payload = parse_notion_payload(results.get("stage7", ""))
    st.session_state.note_payload = parse_notion_payload(results.get("stage8", ""))

# ── results display ─────────────────────────────────────────────────────────
if st.session_state.results:
    results = st.session_state.results
    company = st.session_state.company_name
    b = st.session_state.brief

    st.success("Spec generated.")
    st.divider()

    # top summary always visible
    st.markdown("### Domain & Context")
    st.markdown(results["stage1"])
    st.divider()

    # tabbed view for detailed sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Data Model",
        "API Design",
        "Production Flags",
        "Open Questions",
        "Task Breakdown"
    ])

    with tab1:
        st.markdown(results["stage2"])

    with tab2:
        st.markdown(results["stage3"])

    with tab3:
        st.markdown(results["stage4"])

    with tab4:
        st.markdown(results["stage5"])

    with tab5:
        st.markdown(results["stage6"])

    st.divider()

    # prompts panel collapsed by default
    with st.expander("View prompts used", expanded=False):
        for label, prompt in [
            ("Stage 1 — Extract", stage1_extract(b)),
            ("Stage 2 — Data Model", stage2_data_model(b, results["stage1"])),
            ("Stage 3 — API Design", stage3_api_design(b, results["stage2"])),
            ("Stage 4 — Production Flags", stage4_production_flags(b, results["stage1"])),
            ("Stage 5 — Open Questions", stage5_open_questions(b, results["stage1"], results["stage4"])),
            ("Stage 6 — Task Breakdown", stage6_task_breakdown(results["stage1"], results["stage2"], results["stage3"])),
        ]:
            st.caption(label)
            st.code(prompt)

    st.divider()

    # ── notion push ──────────────────────────────────────────────────────────
    st.markdown("### Push to Notion")

    col_prev1, col_prev2 = st.columns(2)

    with col_prev1:
        with st.expander("Preview tasks payload", expanded=False):
            if st.session_state.notion_payload:
                st.json(st.session_state.notion_payload)
            else:
                st.warning("Could not parse tasks payload.")

    with col_prev2:
        with st.expander("Preview meeting note", expanded=False):
            if st.session_state.note_payload:
                st.markdown(f"**{st.session_state.note_payload.get('title', '')}**")
                st.markdown(st.session_state.note_payload.get("content", ""))
            else:
                st.warning("Could not parse meeting note.")

    if st.session_state.notion_payload:
        if st.button("Send to Notion", use_container_width=True):
            with st.spinner("Pushing to Notion..."):
                meeting_note = st.session_state.note_payload
                notes_to_push = []

                if meeting_note:
                    notes_to_push.append({
                        "title": meeting_note.get("title", "Meeting Note"),
                        "tag": "Meeting",
                        "content": meeting_note.get("content", "")
                    })

                notes_to_push.append({
                    "title": f"{company} — Technical Spec",
                    "tag": "Decision",
                    "content": f"## Data Model\n\n{results['stage2']}\n\n## API Design\n\n{results['stage3']}"
                })

                notes_to_push.append({
                    "title": f"{company} — Production Flags",
                    "tag": "Research",
                    "content": results["stage4"]
                })

                notes_to_push.append({
                    "title": f"{company} — Open Questions",
                    "tag": "Research",
                    "content": results["stage5"]
                })

                push_to_notion(
                    st.session_state.notion_payload,
                    notes_to_push,
                    company
                )
            st.success("Done. Check your Notion workspace.")
    else:
        st.warning("Tasks payload could not be parsed. Try regenerating.")