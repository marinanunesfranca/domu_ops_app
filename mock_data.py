"""
Mock data for the Domu Ops Console MVP.
In production this would be replaced by real queries against the call
platform's database / data warehouse (see Scope of Work, section: Data Layer).
"""

import pandas as pd

CLIENTS = [
    {"client_id": "CLT-001", "name": "Sunrise Collections", "region": "US-East", "timezone": "America/New_York"},
    {"client_id": "CLT-002", "name": "Northbridge Finance", "region": "US-West", "timezone": "America/Los_Angeles"},
    {"client_id": "CLT-003", "name": "Meridian Health Billing", "region": "US-Central", "timezone": "America/Chicago"},
    {"client_id": "CLT-004", "name": "Clearpath Recovery", "region": "US-East", "timezone": "America/New_York"},
    {"client_id": "CLT-005", "name": "Vantage Auto Loans", "region": "US-South", "timezone": "America/Chicago"},
    {"client_id": "CLT-006", "name": "Harborline Utilities", "region": "US-West", "timezone": "America/Los_Angeles"},
    {"client_id": "CLT-007", "name": "Bluepeak Telecom", "region": "US-East", "timezone": "America/New_York"},
]

# ---- Task 2: call outcomes summary ----------------------------------------

CALL_OUTCOMES = pd.DataFrame([
    {"client_id": "CLT-001", "calls_made": 1200, "answered": 740, "paid": 210, "failed": 460},
    {"client_id": "CLT-002", "calls_made": 950,  "answered": 610, "paid": 180, "failed": 340},
    {"client_id": "CLT-003", "calls_made": 1430, "answered": 890, "paid": 265, "failed": 540},
    {"client_id": "CLT-004", "calls_made": 800,  "answered": 480, "paid": 95,  "failed": 320},
    {"client_id": "CLT-005", "calls_made": 1100, "answered": 705, "paid": 240, "failed": 395},
    {"client_id": "CLT-006", "calls_made": 670,  "answered": 410, "paid": 140, "failed": 260},
    {"client_id": "CLT-007", "calls_made": 990,  "answered": 615, "paid": 175, "failed": 375},
])

# ---- Task 3: flagged QA calls ----------------------------------------------

FLAGGED_CALLS = [
    {
        "call_id": "CALL-88213",
        "client_id": "CLT-003",
        "transcript_snippet": "Agent: 'Since you didn't pay, we'll have to report this to the credit bureau today.' Customer hung up.",
        "auto_tag_hint": "possible incorrect statement",
    },
    {
        "call_id": "CALL-88240",
        "client_id": "CLT-001",
        "transcript_snippet": "Call marked as 'payment completed' but no payment confirmation was captured in the transcript.",
        "auto_tag_hint": "possible wrong outcome recorded",
    },
    {
        "call_id": "CALL-88255",
        "client_id": "CLT-005",
        "transcript_snippet": "Agent: 'Hi, this is—' [call ends after 4 seconds, no further audio].",
        "auto_tag_hint": "possible call dropped too early",
    },
    {
        "call_id": "CALL-88299",
        "client_id": "CLT-007",
        "transcript_snippet": "Agent offered a payment plan not listed in the client's approved script options.",
        "auto_tag_hint": "possible incorrect statement",
    },
]

QA_CATEGORIES = [
    "Wrong outcome recorded",
    "Agent said something incorrect",
    "Call dropped too early",
    "Other / needs review",
]

# ---- Task 5: ticket generator ---------------------------------------------

TICKET_TYPES = [
    "New payment option",
    "Prompt / script update",
    "Call flow bug",
    "Reporting / data issue",
    "Compliance-related change",
]

PRIORITIES = ["Low", "Medium", "High", "Urgent"]


def get_client_by_id(client_id: str):
    for c in CLIENTS:
        if c["client_id"] == client_id:
            return c
    return None
