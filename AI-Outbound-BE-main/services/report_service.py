import os
import csv
import tempfile
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

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
    worksheet = workbook.add_worksheet("Report")
    for col, header in enumerate(REPORT_HEADERS):
        worksheet.write(0, col, header)
    for r, row in enumerate(rows, start=1):
        for c, header in enumerate(REPORT_HEADERS):
            worksheet.write(r, c, row.get(header, ""))
    workbook.close()
    return xlsx_out


def email_report(campaign_id: str, recipient_email: str, subject: Optional[str] = None):
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
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = recipient_email
    msg['Subject'] = subject or f"Campaign Report {campaign_id}"
    body = f"Report generated on {datetime.utcnow().isoformat()}Z"
    msg.attach(MIMEText(body, 'plain'))
    with open(attachment_path, 'rb') as f:
        part = MIMEApplication(f.read())
        filename = os.path.basename(attachment_path)
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(part)
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(smtp_user, smtp_password)
    server.sendmail(smtp_user, recipient_email, msg.as_string())
    server.quit()


def cleanup_report(campaign_id: str):
    try:
        csv_path = _csv_path(campaign_id)
        xlsx_out = _xlsx_path(campaign_id)
        if os.path.exists(csv_path):
            os.remove(csv_path)
        if os.path.exists(xlsx_out):
            os.remove(xlsx_out)
    except Exception as e:
        logger.warning(f"Cleanup failed for campaign {campaign_id}: {str(e)}")


def finalize_and_send(campaign_id: str, recipient_email: str, subject: Optional[str] = None):
    email_report(campaign_id, recipient_email, subject)
    cleanup_report(campaign_id)


def are_all_outcomes_complete(campaign_id: str) -> bool:
    path = _csv_path(campaign_id)
    rows = _read_rows(path)
    if not rows:
        return False
    for r in rows:
        if not (r.get("callConnection") or "").strip():
            return False
        if not (r.get("callOutcomes") or "").strip():
            return False
    return True


