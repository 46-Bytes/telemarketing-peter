import os
import csv
import tempfile
import logging
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime
import shutil

try:
    import xlsxwriter  # type: ignore
except Exception:
    xlsxwriter = None

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ── Per-campaign file lock ──
# Multiple concurrent webhooks can read/write the same campaign CSV at the same
# time, corrupting it or causing the completeness check to see stale data.
# We use one lock per campaign_id so different campaigns don't block each other.
_campaign_locks: Dict[str, threading.Lock] = {}
_campaign_locks_meta = threading.Lock()  # protects the dict itself


def _get_campaign_lock(campaign_id: str) -> threading.Lock:
    """Return (or create) a per-campaign threading lock."""
    with _campaign_locks_meta:
        if campaign_id not in _campaign_locks:
            _campaign_locks[campaign_id] = threading.Lock()
        return _campaign_locks[campaign_id]


REPORT_HEADERS = [
    "name",
    "phoneNumber",
    "businessName",
    "NewownerName",
    "NewNumber",
    "BestTimetoCall",
    "callConnection",
    "callOutcomes",
]


def _reports_root() -> str:
    root = os.path.join(tempfile.gettempdir(), "tm_reports")
    os.makedirs(root, exist_ok=True)
    return root


def _campaign_dir(campaign_id: str) -> str:
    base = os.path.join(_reports_root(), campaign_id)
    os.makedirs(base, exist_ok=True)
    return base


def _csv_path(campaign_id: str) -> str:
    return os.path.join(_campaign_dir(campaign_id), f"{campaign_id}.csv")


def _xlsx_path(campaign_id: str) -> str:
    return os.path.join(_campaign_dir(campaign_id), f"{campaign_id}.xlsx")


def init_campaign_report(campaign_id: str, prospects: List[Dict[str, Any]]) -> str:
    """
    Create or reset a temporary CSV for a campaign and seed rows from prospects.
    Each prospect dict should contain name, phoneNumber, businessName.
    """
    path = _csv_path(campaign_id)
    logger.info(f"Initializing campaign report for {campaign_id} at {path}")
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_HEADERS)
        writer.writeheader()
        for p in prospects:
            writer.writerow({
                "name": p.get("name", ""),
                "phoneNumber": p.get("phoneNumber", ""),
                "businessName": p.get("businessName", ""),
                "NewownerName": "",
                "NewNumber": "",
                "BestTimetoCall": "",
                "callConnection": "",
                "callOutcomes": "",
            })
    return path


def seed_rows_if_missing(campaign_id: str, prospects: List[Dict[str, Any]]):
    """
    Ensure the CSV exists and contains a row for each provided prospect phone number.
    Does not overwrite existing rows; adds only missing ones.
    """
    path = _csv_path(campaign_id)
    rows = _read_rows(path)
    if not rows and prospects:
        # Initialize fresh file
        init_campaign_report(campaign_id, prospects)
        return
    existing_numbers = { (r.get("phoneNumber") or "").strip() for r in rows }
    added = False
    for p in prospects:
        pn = (p.get("phoneNumber") or "").strip()
        if not pn or pn in existing_numbers:
            continue
        rows.append({
            "name": p.get("name", ""),
            "phoneNumber": pn,
            "businessName": p.get("businessName", ""),
            "NewownerName": "",
            "NewNumber": "",
            "BestTimetoCall": "",
            "callConnection": "",
            "callOutcomes": "",
        })
        added = True
    if added:
        _write_rows(path, rows)


def _read_rows(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, mode="r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_rows(path: str, rows: List[Dict[str, str]]):
    with open(path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in REPORT_HEADERS})


def update_dynamic_fields(
    campaign_id: str,
    phone_number: str,
    new_owner_name: Optional[str] = None,
    new_number: Optional[str] = None,
    best_time_to_call: Optional[str] = None,
):
    path = _csv_path(campaign_id)
    rows = _read_rows(path)
    if not rows:
        return
    updated = False
    for row in rows:
        if (row.get("phoneNumber") or "").strip() == (phone_number or "").strip():
            if new_owner_name is not None:
                row["NewownerName"] = new_owner_name
            if new_number is not None:
                row["NewNumber"] = new_number
            if best_time_to_call is not None:
                row["BestTimetoCall"] = best_time_to_call
            updated = True
            break
    if updated:
        _write_rows(path, rows)


def update_prospect_name(campaign_id: str, phone_number: str, name: str):
    """Update the prospect name in the report CSV (used when name was missing at upload)."""
    path = _csv_path(campaign_id)
    rows = _read_rows(path)
    if not rows:
        return
    updated = False
    for row in rows:
        if (row.get("phoneNumber") or "").strip() == (phone_number or "").strip():
            if not (row.get("name") or "").strip() or (row.get("name") or "").strip().lower() in ("there", "n/a", "na", "unknown", "none", ""):
                row["name"] = name
                updated = True
            break
    if updated:
        _write_rows(path, rows)


def update_outcome_fields(
    campaign_id: str,
    phone_number: str,
    call_connection: Optional[str] = None,
    call_outcome: Optional[str] = None,
):
    path = _csv_path(campaign_id)
    rows = _read_rows(path)
    if not rows:
        return
    updated = False
    for row in rows:
        if (row.get("phoneNumber") or "").strip() == (phone_number or "").strip():
            if call_connection is not None:
                row["callConnection"] = call_connection
            if call_outcome is not None:
                row["callOutcomes"] = call_outcome
            updated = True
            break
    if updated:
        _write_rows(path, rows)


def _fetch_call_logs(campaign_id: str) -> List[Dict[str, str]]:
    """Fetch call transcript and summary from MongoDB for every prospect in a campaign."""
    try:
        from config.database import get_prospects_collection
        collection = get_prospects_collection()
        prospects = collection.find({"campaignId": campaign_id})
        logs = []
        for prospect in prospects:
            name = prospect.get("name", "")
            phone = prospect.get("phoneNumber", "")
            business = prospect.get("businessName", "")
            calls = prospect.get("calls", [])
            if not calls:
                continue
            # Use the latest call that has a transcript or summary
            for call in reversed(calls):
                transcript = call.get("transcript")
                summary = call.get("callSummary")
                if transcript or summary:
                    logs.append({
                        "name": name,
                        "phoneNumber": phone,
                        "businessName": business,
                        "callSummary": summary or "",
                        "transcript": transcript or "",
                    })
                    break
        return logs
    except Exception as e:
        logger.warning(f"Could not fetch call logs for campaign {campaign_id}: {e}")
        return []


def convert_csv_to_xlsx(campaign_id: str) -> Optional[str]:
    csv_path = _csv_path(campaign_id)
    xlsx_out = _xlsx_path(campaign_id)
    if not os.path.exists(csv_path):
        return None
    if xlsxwriter is None:
        logger.warning("xlsxwriter not available; skipping XLSX conversion")
        return None
    rows = _read_rows(csv_path)
    workbook = xlsxwriter.Workbook(xlsx_out)

    # --- Fetch call transcripts and index by phone number ---
    call_logs = _fetch_call_logs(campaign_id)
    transcript_by_phone = {}
    for log in call_logs:
        phone = (log.get("phoneNumber") or "").strip()
        if phone:
            transcript_by_phone[phone] = log.get("transcript", "")

    # --- Sheet 1: Report (with transcript column) ---
    report_headers_with_transcript = REPORT_HEADERS + ["callTranscript"]
    worksheet = workbook.add_worksheet("Report")
    wrap_format = workbook.add_format({"text_wrap": True, "valign": "top"})
    for col, header in enumerate(report_headers_with_transcript):
        worksheet.write(0, col, header)
    # Set wider column for transcript
    worksheet.set_column(len(REPORT_HEADERS), len(REPORT_HEADERS), 80)
    for r, row in enumerate(rows, start=1):
        for c, header in enumerate(REPORT_HEADERS):
            worksheet.write(r, c, row.get(header, ""))
        # Add transcript from DB for this prospect
        phone = (row.get("phoneNumber") or "").strip()
        transcript = transcript_by_phone.get(phone, "")
        worksheet.write(r, len(REPORT_HEADERS), transcript, wrap_format)

    # --- Sheet 2: Call Logs (transcripts & summaries from DB) ---
    call_log_headers = ["name", "phoneNumber", "businessName", "callSummary", "transcript"]
    call_logs = _fetch_call_logs(campaign_id)
    if call_logs:
        log_sheet = workbook.add_worksheet("Call Logs")
        wrap_format = workbook.add_format({"text_wrap": True, "valign": "top"})
        for col, header in enumerate(call_log_headers):
            log_sheet.write(0, col, header)
        # Set wider columns for summary and transcript
        log_sheet.set_column(3, 3, 50)  # callSummary
        log_sheet.set_column(4, 4, 80)  # transcript
        for r, log in enumerate(call_logs, start=1):
            for c, header in enumerate(call_log_headers):
                log_sheet.write(r, c, log.get(header, ""), wrap_format)

    workbook.close()
    return xlsx_out


def save_report_locally(campaign_id: str) -> Optional[str]:
    """
    Convert the campaign CSV to XLSX and copy it into the project `reports/` folder
    so it is easy to inspect locally.
    """
    xlsx_path = convert_csv_to_xlsx(campaign_id)
    if not xlsx_path or not os.path.exists(xlsx_path):
        return None

    # Project root (one level up from this services/ directory)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    dest_path = os.path.join(reports_dir, f"{campaign_id}.xlsx")
    shutil.copy2(xlsx_path, dest_path)
    logger.info(f"Saved/updated local campaign report for {campaign_id} at {dest_path}")
    return dest_path


def email_report(campaign_id: str, recipient_emails: List[str], subject: Optional[str] = None):
    """Send the campaign report to one or more recipients."""
    smtp_user = os.getenv("SMTP_USER_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")
    if not smtp_user or not smtp_password:
        logger.error("SMTP credentials not configured")
        return
    xlsx_path = convert_csv_to_xlsx(campaign_id)
    attachment_path = xlsx_path if xlsx_path else _csv_path(campaign_id)
    if not os.path.exists(attachment_path):
        logger.error("No report file found to send")
        return

    # Read attachment once
    with open(attachment_path, 'rb') as f:
        attachment_data = f.read()
    filename = os.path.basename(attachment_path)

    for recipient in recipient_emails:
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = recipient
            msg['Subject'] = subject or f"Campaign Report {campaign_id}"
            body = f"Report generated on {datetime.utcnow().isoformat()}Z"
            msg.attach(MIMEText(body, 'plain'))
            part = MIMEApplication(attachment_data)
            part.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(part)
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipient, msg.as_string())
            server.quit()
            logger.info(f"Report emailed to {recipient} for campaign {campaign_id}")
        except Exception as e:
            logger.error(f"Failed to email report to {recipient} for campaign {campaign_id}: {e}")


def cleanup_report(campaign_id: str):
    """Remove temporary files after email is sent.

    We intentionally keep the CSV so that late-arriving duplicate webhooks
    can still read it (and see that outcomes are already complete) rather
    than failing on a missing file.  Only the temp XLSX is removed.
    """
    try:
        xlsx_out = _xlsx_path(campaign_id)
        if os.path.exists(xlsx_out):
            os.remove(xlsx_out)
    except Exception as e:
        logger.warning(f"Cleanup failed for campaign {campaign_id}: {str(e)}")


def finalize_and_send(campaign_id: str, recipient_emails: List[str], subject: Optional[str] = None):
    """
    Convert the CSV to XLSX, save a persistent local copy, email it to all
    recipients, then clean up temp files.  The local copy is saved *before*
    emailing so it is preserved even if SMTP fails.
    """
    # Save the final local copy first (converts CSV → XLSX internally)
    local_path = save_report_locally(campaign_id)
    if local_path:
        logger.info(f"Final local report saved for campaign {campaign_id} at {local_path}")

    # Email the report to all recipients
    email_report(campaign_id, recipient_emails, subject)
    # Remove temp files from the OS temp directory (keeps CSV + local copy)
    cleanup_report(campaign_id)


def are_all_outcomes_complete(campaign_id: str) -> bool:
    path = _csv_path(campaign_id)
    rows = _read_rows(path)
    if not rows:
        return False
    for r in rows:
        # Every row must have a callConnection value (voicemail, successful, etc.)
        # callOutcomes is only populated for successful connections, so we don't
        # require it for non-successful calls.
        connection = (r.get("callConnection") or "").strip()
        if not connection:
            return False
        if connection == "successful" and not (r.get("callOutcomes") or "").strip():
            return False
    return True


