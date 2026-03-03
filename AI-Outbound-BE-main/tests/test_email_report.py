"""
End-to-end test for the email report pipeline.

Exercises: seed → dynamic fields → outcome fields → incremental local save →
           completion check → advisor lookup → finalize & email.
Sends a REAL email to the specified recipient using SMTP credentials from .env.

Usage:
    cd AI-Outbound-BE-main
    python -m tests.test_email_report
"""

import os
import sys

# Ensure project root is on the path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from services.report_service import (
    init_campaign_report,
    seed_rows_if_missing,
    update_dynamic_fields,
    update_outcome_fields,
    are_all_outcomes_complete,
    finalize_and_send,
    save_report_locally,
    _csv_path,
    _read_rows,
)

CAMPAIGN_ID = "test_campaign_002"
RECIPIENT = "zohaibaamer2001@gmail.com"

FAKE_PROSPECTS = [
    {"name": "Alice Johnson", "phoneNumber": "+61412345678", "businessName": "Alice's Bakery"},
    {"name": "Bob Smith", "phoneNumber": "+61423456789", "businessName": "Bob's Auto Repairs"},
    {"name": "Carol Lee", "phoneNumber": "+61434567890", "businessName": "Carol's Consulting"},
]

passed = 0
failed = 0
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_XLSX = os.path.join(BASE_DIR, "reports", f"{CAMPAIGN_ID}.xlsx")


def check(label, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failed += 1
        print(f"  FAIL  {label}")


def main():
    global passed, failed

    # Clean up any leftover test files from a previous run
    if os.path.exists(LOCAL_XLSX):
        os.remove(LOCAL_XLSX)

    print("\n=== Email Report Pipeline Test ===\n")

    # ── Step 1: Seed the report ──────────────────────────────────────────
    print("[Step 1] Seed campaign report with 3 fake prospects")
    path = init_campaign_report(CAMPAIGN_ID, FAKE_PROSPECTS)
    check("CSV file created", os.path.exists(path))

    rows = _read_rows(path)
    check("3 rows seeded", len(rows) == 3)
    check("First row name matches", rows[0].get("name") == "Alice Johnson")
    check("Outcome columns empty initially",
          rows[0].get("callConnection") == "" and rows[0].get("callOutcomes") == "")

    # ── Step 2: Idempotent re-seed ───────────────────────────────────────
    print("\n[Step 2] Re-seed (idempotent) — should NOT duplicate rows")
    seed_rows_if_missing(CAMPAIGN_ID, FAKE_PROSPECTS)
    rows = _read_rows(path)
    check("Still 3 rows after re-seed", len(rows) == 3)

    # ── Step 3: Update dynamic fields ────────────────────────────────────
    print("\n[Step 3] Update dynamic fields (simulating addNewOwnerContact)")
    update_dynamic_fields(
        CAMPAIGN_ID,
        phone_number="+61412345678",
        new_owner_name="David Johnson",
        new_number="+61499999999",
        best_time_to_call="2 PM",
    )
    rows = _read_rows(path)
    alice_row = next(r for r in rows if r["phoneNumber"] == "+61412345678")
    check("NewownerName updated", alice_row["NewownerName"] == "David Johnson")
    check("NewNumber updated", alice_row["NewNumber"] == "+61499999999")
    check("BestTimetoCall updated", alice_row["BestTimetoCall"] == "2 PM")

    # ── Step 4: Partial outcomes + incremental local save ────────────────
    print("\n[Step 4] Update outcomes for 2/3 prospects and verify incremental save")
    update_outcome_fields(CAMPAIGN_ID, "+61412345678", "successful", "meeting booked")
    update_outcome_fields(CAMPAIGN_ID, "+61423456789", "voicemail", "")

    # Simulate what the webhook now does: save_report_locally after each update
    save_report_locally(CAMPAIGN_ID)
    check("Incremental XLSX created after partial outcomes", os.path.exists(LOCAL_XLSX))

    # Verify partial content in the incremental file
    rows = _read_rows(path)
    alice = next(r for r in rows if r["phoneNumber"] == "+61412345678")
    check("Alice outcome recorded", alice["callOutcomes"] == "meeting booked")
    bob = next(r for r in rows if r["phoneNumber"] == "+61423456789")
    check("Bob connection recorded", bob["callConnection"] == "voicemail")
    carol = next(r for r in rows if r["phoneNumber"] == "+61434567890")
    check("Carol still empty", carol["callConnection"] == "" and carol["callOutcomes"] == "")

    check("NOT all complete yet", are_all_outcomes_complete(CAMPAIGN_ID) is False)

    # ── Step 5: Complete all outcomes ────────────────────────────────────
    print("\n[Step 5] Complete remaining outcomes")
    update_outcome_fields(CAMPAIGN_ID, "+61434567890", "successful", "interested in ebook")
    update_outcome_fields(CAMPAIGN_ID, "+61423456789", "voicemail", "no answer")
    check("All outcomes complete", are_all_outcomes_complete(CAMPAIGN_ID) is True)

    # ── Step 6: Finalize and send email ──────────────────────────────────
    print(f"\n[Step 6] Finalize and email report to {RECIPIENT}")
    try:
        finalize_and_send(CAMPAIGN_ID, RECIPIENT, subject="Test Campaign Report (Pipeline Verification)")
        check("finalize_and_send completed without error", True)
    except Exception as e:
        check(f"finalize_and_send failed: {e}", False)

    # ── Step 7: Verify local copy persists after finalize ────────────────
    print("\n[Step 7] Verify local XLSX copy persists")
    check(f"Local XLSX exists at reports/{CAMPAIGN_ID}.xlsx", os.path.exists(LOCAL_XLSX))

    # ── Step 8: Verify temp files cleaned up ─────────────────────────────
    print("\n[Step 8] Verify temp files cleaned up")
    check("Temp CSV removed", not os.path.exists(_csv_path(CAMPAIGN_ID)))

    # ── Summary ──────────────────────────────────────────────────────────
    total = passed + failed
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print(f"All checks passed! Check {RECIPIENT} for the email.")
    else:
        print("Some checks failed — review output above.")
    print(f"{'='*50}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
