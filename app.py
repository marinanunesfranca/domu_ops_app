import streamlit as st
import pandas as pd
import plotly.express as px

from mock_data import (
    CLIENTS,
    CALL_OUTCOMES,
    FLAGGED_CALLS,
    QA_CATEGORIES,
    TICKET_TYPES,
    PRIORITIES,
    get_client_by_id,
)
from llm_helper import generate_call_flow, suggest_qa_category, generate_ticket

st.set_page_config(page_title="Domu Ops Console", page_icon="🎙️", layout="wide")

PAGES = [
    "🏠 Overview",
    "🎙️ Call Script Builder",
    "📊 Client Outcomes Dashboard",
    "🚩 QA Review",
    "🎫 Engineering Ticket Generator",
]

st.sidebar.title("Domu Ops Console")
st.sidebar.caption("MVP — proof of concept for Tech Ops automation")
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")

st.sidebar.markdown("---")
st.sidebar.caption(
    "⚠️ Demo mode: data is mocked and LLM calls use offline templates unless "
    "ANTHROPIC_API_KEY is configured (see llm_helper.py)."
)

# ---------------------------------------------------------------------------
# OVERVIEW
# ---------------------------------------------------------------------------
if page == "🏠 Overview":
    st.title("🎩 Domu Ops Console")
    st.markdown(
        """
This is a proof-of-concept covering **4 of the 7** recurring Tech Ops workflows,
chosen to show breadth of automation across content generation, reporting, and
operational triage:

| # | Task | Screen |
|---|------|--------|
| 1 | Turn a client's raw call script into a structured flow + voice agent prompt | Call Script Builder |
| 2 | Pull & summarize call outcome data across all clients | Client Outcomes Dashboard |
| 3 | Review flagged calls and categorize the issue | QA Review |
| 5 | Turn a client request into an engineering-ready ticket | Engineering Ticket Generator |

Use the sidebar to move between screens. Each screen works standalone with mock
data so it can be demoed without live integrations.
        """
    )
    st.info(
        "See the accompanying **Scope of Work** document for how this MVP maps to "
        "a production build (data pipeline, integrations, auth, compliance guardrails, etc.)."
    )

# ---------------------------------------------------------------------------
# TASK 1 — CALL SCRIPT BUILDER
# ---------------------------------------------------------------------------
elif page == "🎙️ Call Script Builder":
    st.title("🎙️ Call Script Builder")
    st.caption("Task 1 — Turn a new client's raw call script into a structured flow + voice agent prompt")

    client_name = st.text_input("Client name", placeholder="e.g. Sunrise Collections")
    raw_script = st.text_area(
        "Paste the client's raw call script",
        height=220,
        placeholder="Hi, this is [Agent] calling from [Client] regarding your account...",
    )

    if st.button("Generate structured call flow + agent prompt", type="primary"):
        if not raw_script.strip():
            st.warning("Paste a script first.")
        else:
            with st.spinner("Structuring call flow..."):
                output = generate_call_flow(raw_script)
            st.markdown(output)
            st.download_button("Download as .md", output, file_name="call_flow.md")

# ---------------------------------------------------------------------------
# TASK 2 — DASHBOARD
# ---------------------------------------------------------------------------
elif page == "📊 Client Outcomes Dashboard":
    st.title("📊 Client Outcomes Dashboard")
    st.caption("Task 2 — Call outcomes across all 7 active clients")

    df = CALL_OUTCOMES.merge(pd.DataFrame(CLIENTS), on="client_id")
    df["answer_rate"] = (df["answered"] / df["calls_made"] * 100).round(1)
    df["conversion_rate"] = (df["paid"] / df["answered"] * 100).round(1)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total calls", int(df["calls_made"].sum()))
    col2.metric("Total answered", int(df["answered"].sum()))
    col3.metric("Total paid", int(df["paid"].sum()))
    col4.metric("Total failed", int(df["failed"].sum()))

    st.markdown("### Outcomes by client")
    fig = px.bar(
        df,
        x="name",
        y=["answered", "paid", "failed"],
        barmode="group",
        labels={"name": "Client", "value": "Calls", "variable": "Outcome"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Answer rate vs. conversion rate")
    fig2 = px.scatter(
        df, x="answer_rate", y="conversion_rate", text="name", size="calls_made", color="region"
    )
    fig2.update_traces(textposition="top center")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### Raw data")
    st.dataframe(
        df[["client_id", "name", "region", "calls_made", "answered", "paid", "failed",
            "answer_rate", "conversion_rate"]],
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# TASK 3 — QA REVIEW
# ---------------------------------------------------------------------------
elif page == "🚩 QA Review":
    st.title("🚩 QA Review")
    st.caption("Task 3 — Review flagged calls and categorize what went wrong")

    for call in FLAGGED_CALLS:
        client = get_client_by_id(call["client_id"])
        with st.expander(f"{call['call_id']} — {client['name'] if client else call['client_id']}"):
            st.write(f"**Transcript snippet:** {call['transcript_snippet']}")

            if st.button("Suggest category", key=f"suggest_{call['call_id']}"):
                suggestion = suggest_qa_category(call["transcript_snippet"], call["auto_tag_hint"])
                st.markdown(suggestion)

            chosen = st.selectbox(
                "Confirm category",
                QA_CATEGORIES,
                key=f"cat_{call['call_id']}",
            )
            notes = st.text_area("Reviewer notes", key=f"notes_{call['call_id']}", height=80)
            if st.button("Save review", key=f"save_{call['call_id']}"):
                st.success(f"Saved: {call['call_id']} → {chosen}")

# ---------------------------------------------------------------------------
# TASK 5 — TICKET GENERATOR
# ---------------------------------------------------------------------------
elif page == "🎫 Engineering Ticket Generator":
    st.title("🎫 Engineering Ticket Generator")
    st.caption("Task 5 — Turn a client request into an engineering-ready ticket")

    client_options = {f"{c['name']} ({c['client_id']})": c for c in CLIENTS}
    chosen_label = st.selectbox("Client", list(client_options.keys()))
    client = client_options[chosen_label]

    ticket_type = st.selectbox("Ticket type", TICKET_TYPES)
    priority = st.selectbox("Priority", PRIORITIES)
    description = st.text_area(
        "Describe the request as reported by the client",
        placeholder="Client wants to add Apple Pay as a payment option for their outbound collections calls.",
        height=140,
    )

    if st.button("Generate ticket", type="primary"):
        if not description.strip():
            st.warning("Add a description first.")
        else:
            with st.spinner("Drafting ticket..."):
                ticket = generate_ticket(client, ticket_type, priority, description)
            st.markdown(ticket)
            st.download_button("Download as .md", ticket, file_name="engineering_ticket.md")
