"""
Single place where this MVP would call out to an LLM (e.g. Claude via the
Anthropic API). Isolated here so:
  1) It's obvious to reviewers/engineers where "real" generation happens.
  2) The rest of the app works even without an API key configured
     (falls back to a clearly-labeled template response), so the demo
     never breaks live.

To go live: set ANTHROPIC_API_KEY as an environment variable / Streamlit
secret and flip USE_LIVE_LLM to True.
"""

import os

USE_LIVE_LLM = False  # flip to True once ANTHROPIC_API_KEY is set in secrets


def _call_claude(system: str, user_prompt: str) -> str:
    """Real call to the Anthropic API. Only used if USE_LIVE_LLM is True."""
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def generate_call_flow(raw_script: str) -> str:
    """Task 1: turn a raw client call script into a structured call flow + voice agent prompt."""
    system = (
        "You are a conversation designer for an outbound voice AI collections agent. "
        "Given a raw call script from a client, produce: "
        "1) a structured call flow (greeting, verification, purpose, objection handling, "
        "payment capture, closing, fallback/escalation paths) as numbered steps with branches, "
        "2) a ready-to-use system prompt for the voice agent that encodes tone, compliance "
        "guardrails (no threats, no false statements about credit reporting, always allow opt-out), "
        "and the branching logic."
    )
    if USE_LIVE_LLM:
        return _call_claude(system, raw_script)

    # Offline fallback so the demo works without a live key.
    return f"""**[DEMO MODE — offline template output. Plug in ANTHROPIC_API_KEY for live generation]**

**Structured Call Flow**
1. Greeting & identity disclosure
2. Identity verification (2 data points)
3. State purpose of call (balance/payment reminder)
4. Present payment options
   4a. If objection → route to Objection Handling
   4b. If agrees to pay → route to Payment Capture
5. Objection Handling (branches: "can't afford", "dispute the debt", "already paid")
6. Payment Capture (amount, method, confirmation read-back)
7. Compliance disclosures (mini-Miranda, opt-out reminder)
8. Closing / call summary
9. Fallback: if customer requests human agent or shows distress → escalate

**Generated Voice Agent System Prompt (draft)**
"You are a payment reminder assistant calling on behalf of {{client_name}}. Verify identity
before discussing account details. Never state or imply legal consequences, credit bureau
reporting, or wage garnishment unless explicitly authorized in the client's approved script.
If the customer disputes the debt or asks to stop being contacted, acknowledge and follow the
opt-out flow immediately. Keep responses under 2 sentences. Escalate to a human if the customer
expresses hardship or distress."

Raw script received ({len(raw_script)} chars) would be parsed here to extract client-specific
terms, payment options, and any client-approved disclosures.
"""


def suggest_qa_category(transcript_snippet: str, hint: str) -> str:
    """Task 3: suggest a QA category for a flagged call."""
    if USE_LIVE_LLM:
        system = "Classify this flagged call snippet into exactly one QA category and explain briefly why."
        return _call_claude(system, transcript_snippet)
    return f"[DEMO MODE] Suggested category based on pattern match: **{hint}**. Confirm or override below."


def extract_ticket_from_call(transcript_snippet: str, detected_request: str) -> str:
    """
    Task 5 (automated path): given a call transcript that has already been
    flagged as containing an actionable request, draft the ticket description
    an engineer would need — without a human having to type it up first.
    In production this would run as a background job right after the call ends.
    """
    if USE_LIVE_LLM:
        system = (
            "You are drafting an engineering ticket description from a call transcript "
            "snippet. Be specific about what the customer/client asked for and any "
            "relevant context from the call. Do not invent details not present in the transcript."
        )
        return _call_claude(system, f"Detected request: {detected_request}\nTranscript: {transcript_snippet}")

    return (
        f"[DEMO MODE] Based on the call transcript, the customer/client raised the "
        f"following: \"{detected_request}\". Relevant excerpt: \"{transcript_snippet}\". "
        f"Recommend confirming feasibility and rollout scope with the client before implementation."
    )


def generate_ticket(client, ticket_type, priority, description) -> str:
    """Task 5: turn a reported issue into an engineering-ready ticket."""
    if USE_LIVE_LLM:
        system = (
            "Write a clear, actionable engineering ticket (title, context, acceptance criteria, "
            "affected client, priority) from the following report."
        )
        user_prompt = (
            f"Client: {client}\nType: {ticket_type}\nPriority: {priority}\nReport: {description}"
        )
        return _call_claude(system, user_prompt)

    client_name = client["name"] if client else "Unknown client"
    client_id = client["client_id"] if client else "N/A"
    return f"""**[DEMO MODE — template output]**

**Title:** [{ticket_type}] {client_name} — {description[:60]}{'...' if len(description) > 60 else ''}

**Client:** {client_name} ({client_id})
**Priority:** {priority}
**Type:** {ticket_type}

**Context:**
{description}

**Acceptance Criteria:**
- [ ] Change implemented and covered by the agent's call flow / config for {client_id} only
- [ ] Verified in staging with a test call before enabling in production
- [ ] Client notified once live

**Notes for engineering:**
Auto-populated from client account data. Confirm scope with client success before starting.
"""
