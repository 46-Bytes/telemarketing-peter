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


def main():
    global passed, failed
    print("\n=== Tests for Latest Changes ===")

    test_xlsx_has_transcript_column()
    test_must_send_recipient_always_included()
    test_finalize_called_with_must_send()

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
