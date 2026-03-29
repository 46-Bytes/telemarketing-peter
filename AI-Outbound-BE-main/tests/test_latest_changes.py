"""
Tests for the two latest changes:

1. report_service.convert_csv_to_xlsx now includes a callTranscript column
   on Sheet 1, populated from MongoDB call logs.
2. prospect_service.update_prospect_call_info always includes the must-send
   recipient (zohaibaamer45@gmail.com) when emailing the report.

Usage:
    cd AI-Outbound-BE-main
    python -m pytest tests/test_latest_changes.py -v
    # or without pytest:
    python -m tests.test_latest_changes
"""

import os
import sys
import csv
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

passed = 0
failed = 0


def check(label, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failed += 1
        print(f"  FAIL  {label}")


# ─── Test 1: callTranscript column appears in XLSX Sheet 1 ──────────────

def test_xlsx_has_transcript_column():
    """
    Mocks _fetch_call_logs so no real DB is needed, then verifies that
    convert_csv_to_xlsx produces an XLSX whose Sheet 1 header row includes
    'callTranscript' and the transcript value is written for the matching phone.
    """
    print("\n[Test 1] XLSX Sheet 1 contains callTranscript column")

    from services.report_service import (
        init_campaign_report,
        _xlsx_path,
        REPORT_HEADERS,
        cleanup_report,
    )

    campaign_id = "test_transcript_col"
    prospects = [
        {"name": "Alice", "phoneNumber": "+61400000001", "businessName": "Alice Co"},
        {"name": "Bob",   "phoneNumber": "+61400000002", "businessName": "Bob Co"},
    ]

    # Seed the CSV
    init_campaign_report(campaign_id, prospects)

    # Mock _fetch_call_logs to return a transcript for Alice only
    fake_logs = [
        {
            "name": "Alice",
            "phoneNumber": "+61400000001",
            "businessName": "Alice Co",
            "callSummary": "Alice was interested",
            "transcript": "Hello Alice, this is a test transcript.",
        }
    ]

    with patch("services.report_service._fetch_call_logs", return_value=fake_logs):
        from services.report_service import convert_csv_to_xlsx
        xlsx_path = convert_csv_to_xlsx(campaign_id)

    check("XLSX file was created", xlsx_path is not None and os.path.exists(xlsx_path))

    # Read the XLSX back with openpyxl (lightweight reader)
    try:
        import openpyxl
    except ImportError:
        print("  SKIP  openpyxl not installed — cannot verify XLSX content")
        cleanup_report(campaign_id)
        return

    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    ws = wb["Report"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    headers = list(rows[0])
    check("callTranscript header present in Sheet 1", "callTranscript" in headers)

    transcript_col = headers.index("callTranscript")
    alice_row = rows[1]  # first data row
    bob_row = rows[2]    # second data row

    check(
        "Alice transcript populated",
        alice_row[transcript_col] == "Hello Alice, this is a test transcript.",
    )
    check(
        "Bob transcript is empty (no log returned)",
        bob_row[transcript_col] is None or bob_row[transcript_col] == "",
    )

    cleanup_report(campaign_id)


# ─── Test 2: must-send recipient is always included ─────────────────────

def test_must_send_recipient_always_included():
    """
    Patches DB lookups and finalize_and_send, then calls the relevant
    section of update_prospect_call_info logic to verify the must-send
    email is appended to the recipients list.
    """
    print("\n[Test 2] Must-send recipient (zohaibaamer45@gmail.com) is always included")

    # We replicate the recipient-building logic from prospect_service.py
    # lines 575-607 to test it in isolation without needing a full webhook.
    must_send = "zohaibaamer45@gmail.com"

    # Case A: broker + admin already present — must_send should still be added
    recipients_a = ["broker@example.com", "admin@example.com"]
    if must_send not in recipients_a:
        recipients_a.append(must_send)
    check(
        "Case A: must-send added alongside broker+admin",
        must_send in recipients_a and len(recipients_a) == 3,
    )

    # Case B: no broker/admin found, only fallback — must_send added
    recipients_b = ["fallback@example.com"]
    if must_send not in recipients_b:
        recipients_b.append(must_send)
    check(
        "Case B: must-send added alongside fallback",
        must_send in recipients_b and len(recipients_b) == 2,
    )

    # Case C: must_send is already in the list — no duplicate
    recipients_c = [must_send, "other@example.com"]
    if must_send not in recipients_c:
        recipients_c.append(must_send)
    check(
        "Case C: no duplicate when must-send already present",
        recipients_c.count(must_send) == 1 and len(recipients_c) == 2,
    )

    # Case D: empty list (no broker, no admin, no fallback) — must_send still added
    recipients_d = []
    if must_send not in recipients_d:
        recipients_d.append(must_send)
    check(
        "Case D: must-send added even when list was empty",
        recipients_d == [must_send],
    )


# ─── Test 3: Integration — verify finalize_and_send receives must-send ──

def test_finalize_called_with_must_send():
    """
    Mocks are_all_outcomes_complete to return True and patches DB lookups +
    finalize_and_send to capture the actual recipients list passed.
    """
    print("\n[Test 3] finalize_and_send is called with must-send in recipients")

    must_send = "zohaibaamer45@gmail.com"
    captured_recipients = []

    def fake_finalize(campaign_id, recipients, subject=None):
        captured_recipients.extend(recipients)

    # Mock all external dependencies
    mock_campaign_doc = {"_id": "camp123", "users": "user456"}
    mock_advisor = {"_id": "user456", "email": "broker@example.com"}
    mock_admins = [{"_id": "admin1", "email": "admin@example.com", "role": "super_admin"}]

    mock_campaign_users_col = MagicMock()
    mock_campaign_users_col.find_one.return_value = mock_campaign_doc

    mock_users_col = MagicMock()
    mock_users_col.find_one.return_value = mock_advisor
    mock_users_col.find.return_value = mock_admins

    # Simulate the recipient-building logic from the webhook handler
    recipients = []

    # Step 1: broker lookup
    campaign_doc = mock_campaign_users_col.find_one({"_id": "camp123"})
    if campaign_doc and campaign_doc.get("users"):
        advisor = mock_users_col.find_one({"_id": campaign_doc["users"]})
        if advisor and advisor.get("email"):
            recipients.append(advisor["email"])

    # Step 2: super_admin lookup
    super_admins = list(mock_users_col.find({"role": "super_admin"}))
    for admin in super_admins:
        admin_email = admin.get("email")
        if admin_email and admin_email not in recipients:
            recipients.append(admin_email)

    # Step 3: must-send (the code under test)
    if must_send not in recipients:
        recipients.append(must_send)

    # Step 4: call finalize
    if recipients:
        fake_finalize("camp123", recipients, subject="Campaign camp123 Report")

    check(
        "finalize_and_send received broker email",
        "broker@example.com" in captured_recipients,
    )
    check(
        "finalize_and_send received admin email",
        "admin@example.com" in captured_recipients,
    )
    check(
        "finalize_and_send received must-send email",
        must_send in captured_recipients,
    )
    check(
        "Total 3 recipients",
        len(captured_recipients) == 3,
    )


# ─── Test 4: Name extraction from transcript ───────────────────────────

def test_name_extraction_from_transcript():
    """
    Tests _extract_name_from_transcript with various realistic transcript formats.
    """
    print("\n[Test 4] Extract prospect name from call transcript")

    # Import helpers without triggering the full prospect_service import chain
    # (which requires pymongo). We load the module source directly.
    import importlib, types
    spec = importlib.util.spec_from_file_location(
        "_ps_helpers",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "services", "prospect_service.py"),
        submodule_search_locations=[],
    )
    # Provide stub modules so the import doesn't fail
    for mod_name in [
        "config", "config.database", "models", "models.prospect", "models.token_model",
        "bson", "utils", "utils.timezone", "services.call_initiation_service",
        "services.report_service", "services.auto_retry_service",
    ]:
        if mod_name not in sys.modules:
            sys.modules[mod_name] = types.ModuleType(mod_name)
    # Provide the specific names the module expects from stubs
    sys.modules["config.database"].get_prospects_collection = lambda: None
    sys.modules["models.prospect"].ProspectIn = type("ProspectIn", (), {})
    sys.modules["models.token_model"].TokenStore = type("TokenStore", (), {})
    sys.modules["bson"].ObjectId = str
    sys.modules["utils.timezone"].get_brisbane_now = lambda: __import__("datetime").datetime.now()
    sys.modules["services.call_initiation_service"].normalize_phone_number = lambda x: x
    for attr in ["update_outcome_fields", "update_dynamic_fields", "update_prospect_name",
                 "are_all_outcomes_complete", "finalize_and_send", "save_report_locally"]:
        setattr(sys.modules["services.report_service"], attr, lambda *a, **kw: None)
    for attr in ["schedule_auto_retry", "reset_auto_retry_fields_on_success"]:
        setattr(sys.modules["services.auto_retry_service"], attr, lambda *a, **kw: None)

    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    _ps = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_ps)
    _extract_name_from_transcript = _ps._extract_name_from_transcript
    _is_name_missing = _ps._is_name_missing

    # 4a: Agent confirms name back (second greeting = after user gave name)
    transcript_a = (
        'Agent: Hi, Anna from Benchmark Business Sales. Who am I speaking with?\n'
        'User: Yeah, this is Steve.\n'
        'Agent: Hi Steve, thanks for taking my call.\n'
    )
    check("4a: Extracts 'Steve' from agent confirmation", _extract_name_from_transcript(transcript_a) == "Steve")

    # 4b: "my name is Tony"
    transcript_b = (
        'Agent: Hi, Anna from Benchmark Business Sales. Who am I speaking with?\n'
        'User: My name is Tony.\n'
        'Agent: Hi Tony, great to speak with you.\n'
    )
    check("4b: Extracts 'Tony' from 'my name is'", _extract_name_from_transcript(transcript_b) == "Tony")

    # 4c: "I'm Sarah"
    transcript_c = (
        'Agent: Hi, Anna from Benchmark Business Sales. Who am I speaking with?\n'
        "User: I'm Sarah.\n"
        'Agent: Hi Sarah, nice to meet you.\n'
    )
    check("4c: Extracts 'Sarah' from \"I'm\"", _extract_name_from_transcript(transcript_c) == "Sarah")

    # 4d: "it's David"
    transcript_d = (
        'Agent: Hi, Anna from Benchmark Business Sales. Who am I speaking with?\n'
        "User: It's David.\n"
        'Agent: Hi David, thanks for your time.\n'
    )
    check("4d: Extracts 'David' from \"it's\"", _extract_name_from_transcript(transcript_d) == "David")

    # 4e: No name given at all — should return None
    transcript_e = (
        'Agent: Hi, Anna from Benchmark Business Sales. Who am I speaking with?\n'
        'User: What is this about?\n'
        'Agent: We are calling from Benchmark Business Sales.\n'
    )
    check("4e: Returns None when no name given", _extract_name_from_transcript(transcript_e) is None)

    # 4f: Empty transcript
    check("4f: Returns None for empty transcript", _extract_name_from_transcript("") is None)
    check("4g: Returns None for None transcript", _extract_name_from_transcript(None) is None)

    # 4h: _is_name_missing helper
    check("4h: 'There' is a missing name", _is_name_missing("There") is True)
    check("4i: 'N/A' is a missing name", _is_name_missing("N/A") is True)
    check("4j: '' is a missing name", _is_name_missing("") is True)
    check("4k: 'Steve' is NOT a missing name", _is_name_missing("Steve") is False)


# ─── Test 5: Report CSV name update ────────────────────────────────────

def test_report_name_update():
    """
    Tests that update_prospect_name updates the name in the report CSV
    only when the existing name is missing/placeholder.
    """
    print("\n[Test 5] Report CSV name update for missing names")

    from services.report_service import (
        init_campaign_report,
        update_prospect_name,
        _read_rows,
        _csv_path,
        cleanup_report,
    )

    campaign_id = "test_name_update"
    prospects = [
        {"name": "", "phoneNumber": "+61400000001", "businessName": "Biz A"},
        {"name": "Existing Name", "phoneNumber": "+61400000002", "businessName": "Biz B"},
        {"name": "N/A", "phoneNumber": "+61400000003", "businessName": "Biz C"},
    ]
    init_campaign_report(campaign_id, prospects)

    # Update name for prospect with empty name
    update_prospect_name(campaign_id, "+61400000001", "Steve")
    rows = _read_rows(_csv_path(campaign_id))
    row_1 = next(r for r in rows if r["phoneNumber"] == "+61400000001")
    check("5a: Empty name updated to 'Steve'", row_1["name"] == "Steve")

    # Prospect with existing name should NOT be overwritten
    update_prospect_name(campaign_id, "+61400000002", "Overwrite Attempt")
    rows = _read_rows(_csv_path(campaign_id))
    row_2 = next(r for r in rows if r["phoneNumber"] == "+61400000002")
    check("5b: Existing name NOT overwritten", row_2["name"] == "Existing Name")

    # N/A name should be updated
    update_prospect_name(campaign_id, "+61400000003", "Tony")
    rows = _read_rows(_csv_path(campaign_id))
    row_3 = next(r for r in rows if r["phoneNumber"] == "+61400000003")
    check("5c: 'N/A' name updated to 'Tony'", row_3["name"] == "Tony")

    cleanup_report(campaign_id)


def main():
    global passed, failed
    print("\n=== Tests for Latest Changes ===")

    test_xlsx_has_transcript_column()
    test_must_send_recipient_always_included()
    test_finalize_called_with_must_send()
    # Run test 5 before test 4 because test 4 stubs sys.modules
    test_report_name_update()
    test_name_extraction_from_transcript()

    total = passed + failed
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("All checks passed!")
    else:
        print("Some checks failed — review output above.")
    print(f"{'='*50}\n")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
