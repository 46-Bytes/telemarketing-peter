# New Owner Data & Call Report Implementation

## Overview
This document describes the implementation of the new owner data capture feature and comprehensive call reporting system.

## Features Implemented

### 1. New Owner Data Capture
When a contact indicates they are not the business owner, the AI collects:
- **Owner's Full Name** - The actual business owner's name
- **Owner's Phone Number** - Best contact number for the owner
- **Best Time to Call** - Preferred date/time to contact the owner

#### Flow:
1. AI asks for owner details during the call
2. AI immediately calls the `AddNewOwner` function via Retell
3. Backend endpoint `/api/add_newowner_contact` receives the data
4. Data is stored in:
   - MongoDB prospect collection (fields: `newOwnerName`, `newOwnerPhone`, `bestTimeToCall`)
   - Campaign report CSV (columns: `NewownerName`, `NewNumber`, `BestTimetoCall`)

### 2. Call Report Generation

#### Report Fields:
The campaign report includes the following columns:
1. **name** - Contact person's name
2. **phoneNumber** - Dialed phone number
3. **businessName** - Business name
4. **NewownerName** - New owner's name (if provided)
5. **NewNumber** - New owner's phone number (if provided)
6. **BestTimetoCall** - Best time to contact (if provided)
7. **callConnection** - Connection status:
   - `successful` - Call was answered
   - `unsuccessful no pick up` - No answer
   - `voicemail` - Went to voicemail
8. **callOutcomes** - Call outcome (for successful calls):
   - `meeting booked` - Appointment scheduled
   - `interested in ebook` - Requested ebook
   - `no interest` - Not interested
   - `user hung up` - Hung up during call
   - `callback requested` - Requested callback
   - `successful` - Call completed normally

#### Report Flow:
1. **Initialization**: When calls are initiated, report CSV is created with all prospect rows
2. **During Call**: If AI captures new owner data, it's immediately stored
3. **Call Completion**: Webhook updates connection status and outcomes
4. **Finalization**: When all calls complete, report is:
   - Converted to Excel (.xlsx)
   - Emailed to configured recipient
   - Cleaned up from temporary storage

### 3. API Endpoints

#### POST `/api/add_newowner_contact`
Handles new owner data from Retell function calls.

**Request Body:**
```json
{
  "campaignId": "string",
  "phoneNumber": "string",
  "newOwnerName": "string (optional)",
  "newNumber": "string (optional)",
  "bestTimeToCall": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "message": "New owner data captured successfully"
}
```

### 4. Webhook Enhancement

#### POST `/webhook`
Enhanced to extract and store comprehensive call data.

**New Data Extracted:**
- Call connection status (successful/unsuccessful/voicemail)
- Call outcomes (meeting/ebook/no interest/hung up/callback)
- Custom analysis data from Retell
- Automatic report finalization when campaign completes

### 5. Database Schema Updates

#### Prospect Model (MongoDB):
```javascript
{
  // ... existing fields ...
  newOwnerName: String,      // New owner's name
  newOwnerPhone: String,     // New owner's phone number
  bestTimeToCall: String     // Best time to contact
}
```

### 6. Email Configuration

Reports are sent automatically when all campaign calls complete.

**Environment Variables Required:**
```bash
SMTP_USER_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
REPORT_RECIPIENT_EMAIL=recipient@example.com  # Optional, defaults to SMTP_USER_EMAIL
```

**Email Contains:**
- Subject: "Campaign {campaign_id} Report"
- Attachment: Excel file with complete call data
- Includes all prospect data, new owner info, and call outcomes

## Usage

### For AI Agent (Retell):
The AI prompt instructs to call the `AddNewOwner` function when owner details are collected:
```
- Immediately after collecting these details, call the AddNewOwner function with:
  - campaignId: {{campaign_id}}
  - phoneNumber: the dialed number (the phone number you called)
  - newOwnerName: the owner's full name provided
  - newNumber: the owner's best direct number provided
  - bestTimeToCall: the best time/date to contact them provided
```

### For Backend:
1. **Start Campaign**: Report is automatically initialized when calls begin
2. **During Calls**: 
   - New owner data captured via API calls
   - Call progress tracked in real-time
3. **Campaign End**: 
   - Report automatically sent when last call completes
   - Recipients receive Excel attachment

## File Changes

### Modified Files:
1. `models/prospect.py` - Added new owner fields to model
2. `routes/prospects_route.py` - Activated AddNewOwner endpoint
3. `services/prospect_service.py` - Enhanced webhook to extract outcomes
4. `services/call_initiation_service.py` - Added report initialization
5. `services/report_service.py` - Already had required structure (no changes needed)
6. `prompt.txt` - Updated AI instructions for AddNewOwner function

### Report Service Functions Used:
- `seed_rows_if_missing()` - Initialize report with prospects
- `update_dynamic_fields()` - Update new owner data
- `update_outcome_fields()` - Update call connection and outcomes
- `are_all_outcomes_complete()` - Check if all calls finished
- `finalize_and_send()` - Convert to Excel and email report

## Testing

### Test New Owner Data Capture:
1. Start a campaign with test prospects
2. During call, tell AI you're not the owner
3. Provide owner name, number, and best time to call
4. Verify data appears in report

### Test Call Outcomes:
1. Complete various call scenarios:
   - Book a meeting
   - Request ebook
   - Express no interest
   - Hang up
   - Request callback
2. Check report for accurate outcomes

### Test Report Email:
1. Complete all calls in a campaign
2. Verify email sent with Excel attachment
3. Check all columns populated correctly

## Troubleshooting

### Report Not Sent:
- Check `SMTP_USER_EMAIL` and `SMTP_PASSWORD` are configured
- Check `REPORT_RECIPIENT_EMAIL` or default recipient exists
- Check logs for "All calls complete" message
- Verify `are_all_outcomes_complete()` returns true

### New Owner Data Not Captured:
- Check Retell function call logs
- Verify endpoint `/api/add_newowner_contact` is accessible
- Check MongoDB for `newOwnerName`, `newOwnerPhone`, `bestTimeToCall` fields
- Check report CSV for populated columns

### Call Outcomes Incorrect:
- Check webhook logs for extracted outcomes
- Verify custom_analysis_data from Retell contains expected fields
- Check outcome mapping logic in `update_prospect_call_info()`

## Future Enhancements

Potential improvements:
1. Dashboard UI to view reports in real-time
2. Multiple recipient emails for reports
3. Scheduled report summaries (daily/weekly)
4. Advanced filtering and analytics
5. Export formats (PDF, CSV) in addition to Excel

## Notes

- Reports are stored temporarily and cleaned up after emailing
- Excel conversion requires `xlsxwriter` package
- Reports are organized by `campaign_id` in temp directory
- New owner data can be updated multiple times during a campaign
- Call outcomes only populated for successful connections





