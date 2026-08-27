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

from mock_data import QA_CATEGORIES

USE_LIVE_LLM = True  # flip to True once ANTHROPIC_API_KEY is set in secrets


def _call_claude(system: str, user_prompt: str) -> str:
    """Real call to the Anthropic API. Only used if USE_LIVE_LLM is True."""
    import anthropic

    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def generate_call_flow(raw_script: str) -> str:
    """Task 1: turn a raw client call script into a structured call flow + voice agent prompt."""
    system = """You are a senior conversation designer building outbound voice AI agents for debt collection and payment reminder calls.

You will be given a client's raw call script (as used by human agents today). Convert it into two things, and output ONLY the following, in this exact structure:

## Structured Call Flow
A numbered list of call stages (greeting, identity verification, purpose, payment options, objection handling, payment capture, compliance disclosures, closing). For any stage with branches (e.g. objection handling), use lettered sub-steps (4a, 4b...) showing the condition and where it routes.

## Voice Agent System Prompt
A complete, ready-to-paste system prompt for the voice agent, written in second person ("You are..."), that:
- Encodes the tone and specific language actually present in the client's raw script (don't genericize it away)
- Never states or implies legal consequences, credit bureau reporting, wage garnishment, or arrest unless that exact language appears in the client's raw script
- Always includes an opt-out / do-not-call path
- Instructs the agent to escalate to a human if the customer expresses hardship, distress, or disputes the debt
- Keeps individual agent responses short (1-2 sentences)

Hard rules:
- Do not invent payment methods, amounts, or legal claims not present in the raw script.
- If the raw script is missing something essential (e.g. no verification step), flag it in a final "## Gaps to confirm with client" section instead of inventing content.
- Do not include any preamble, meta-commentary, or text outside the three headers above."""

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
        categories_list = "\n".join(f"- {c}" for c in QA_CATEGORIES)
        system = f"""You are a QA reviewer for outbound voice AI collections calls.

Given a transcript snippet from a flagged call, choose EXACTLY ONE category from this closed list (do not invent a new one):
{categories_list}

Output in this exact format, nothing else:
**Category:** <one category from the list, verbatim>
**Why:** <one sentence, referencing specific evidence from the transcript>"""
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
        system = """You are drafting the "description" field of an engineering ticket, based on a flagged call transcript. This is NOT the full ticket — just a 2-4 sentence description an engineer would read to understand the request.

Write it to:
- State plainly what was asked for or what problem occurred, in plain business language (not a transcript quote)
- Include any concrete detail present in the transcript that would affect implementation (e.g. a specific payment method named, a specific condition under which a bug occurs)
- End with one open question or dependency an engineer would need answered before starting, if one is evident from the transcript

Do not invent details not present in the transcript or detected request. Do not include a title, headers, or acceptance criteria — just the description text."""
        return _call_claude(system, f"Detected request: {detected_request}\nTranscript: {transcript_snippet}")

    return (
        f"[DEMO MODE] Based on the call transcript, the customer/client raised the "
        f"following: \"{detected_request}\". Relevant excerpt: \"{transcript_snippet}\". "
        f"Recommend confirming feasibility and rollout scope with the client before implementation."
    )


def generate_ticket(client, ticket_type, priority, description) -> str:
    """Task 5: turn a reported issue into an engineering-ready ticket."""
    if USE_LIVE_LLM:
        client_name = client["name"] if client else "Unknown client"
        client_id = client["client_id"] if client else "N/A"
        system = f"""You are a Technical Ops Lead writing an engineering ticket from a client request or reported issue. Write ONLY the ticket, in exactly this Markdown structure and nothing else:

**Title:** [{ticket_type}] {client_name} — <5-8 word summary of the specific request>

**Client:** {client_name} ({client_id})
**Priority:** {priority}
**Type:** {ticket_type}

**Context:**
<2-4 sentences explaining the request/issue in plain business language, using only details given below>

**Acceptance Criteria:**
- [ ] <specific, testable criterion tied to this exact request>
- [ ] <verification step, e.g. staging test before enabling in production>
- [ ] <rollout/communication step if relevant, e.g. notifying the client once live>

**Notes for engineering:**
<any open question, dependency, or scope boundary an engineer should know before starting — only include if evident from the report, otherwise omit this line>

Do not invent scope, payment amounts, or technical implementation details not implied by the report below."""
        user_prompt = (
            f"Client: {client_name} ({client_id})\nType: {ticket_type}\nPriority: {priority}\nReport: {description}"
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
