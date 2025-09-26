from bson import ObjectId
from services.prospect_service import get_prospects_collection
from datetime import datetime
from config.database import get_users_collection

def get_total_calls_made(userId: str):
    """Calculate the total number of calls made."""
    collection = get_prospects_collection()
    users_collection = get_users_collection()

    # Check if user is a super_admin
    user = users_collection.find_one({"name": userId})
    is_super_admin = user and user.get("role") == "super_admin"

    # Build match stage
    match_stage = {"calls.status": "ended"}

    # Only add ownerName if not outbound and not a super_admin
    if not is_super_admin:
        match_stage["ownerName"] = userId

    total_calls = collection.aggregate([
        {"$match": match_stage},
        {"$unwind": "$calls"},
        {"$count": "totalCalls"}
    ])
    result = next(total_calls, {"totalCalls": 0})
    return result["totalCalls"]

def get_connected_calls(userId: str):
    """Calculate the total number of calls with status 'ended'."""
    collection = get_prospects_collection()
    users_collection = get_users_collection()

    # Check if user is a super_admin
    user = users_collection.find_one({"name": userId})
    is_super_admin = user and user.get("role") == "super_admin"

    # Build match stage
    match_stage = {"calls.status": "ended"}

    # Only add ownerName if not outbound and not a super_admin
    if not is_super_admin:
        match_stage["ownerName"] = userId

    total_connected_calls = collection.aggregate([
        {"$match": match_stage},
        {"$unwind": "$calls"},
        {"$count": "totalConnectedCalls"}
    ])
    result = next(total_connected_calls, {"totalConnectedCalls": 0})
    return result["totalConnectedCalls"]

def get_appointments_booked(userId: str):
    """Calculate the total number of appointments booked based on appointmentInterest."""
    collection = get_prospects_collection()
    users_collection = get_users_collection()

    # Check if user is a super_admin
    user = users_collection.find_one({"name": userId})
    is_super_admin = user and user.get("role") == "super_admin"

    # Build match stage
    match_stage = {"appointment.appointmentInterest": True}

    # Only add ownerName if not outbound and not a super_admin
    if not is_super_admin:
        match_stage["ownerName"] = userId

 
    appointments_booked = collection.aggregate([
        {"$match": match_stage},
        {"$count": "totalAppointmentsBooked"}
    ])
    result = next(appointments_booked, {"totalAppointmentsBooked": 0})
    return result["totalAppointmentsBooked"]

def get_number_of_ebooks_sent(userId: str):
    """Calculate the total number of ebooks sent based on isEbook and user role."""
    collection = get_prospects_collection()
    users_collection = get_users_collection()

    # Check if user is a super_admin
    user = users_collection.find_one({"name": userId})
    is_super_admin = user and user.get("role") == "super_admin"

    # Build match stage
    match_stage = {"isEbook": True}

    # Only add ownerName if not outbound and not a super_admin
    if not is_super_admin:
        match_stage["ownerName"] = userId

    pipeline = [
        {"$match": match_stage},
        {"$count": "totalEbooksSent"}
    ]

    total_ebooks_sent = collection.aggregate(pipeline)
    result = next(total_ebooks_sent, {"totalEbooksSent": 0})
    return result["totalEbooksSent"]

def get_average_call_duration(userId: str):
    """Calculate the average call duration."""

    collection = get_prospects_collection()
    users_collection = get_users_collection()

    # Check if user is a super_admin
    user = users_collection.find_one({"name": userId})
    is_super_admin = user and user.get("role") == "super_admin"

    pipeline = [
        {"$match": {"calls.status": "ended"}},
        {"$unwind": "$calls"},
        {"$group": {"_id": None, "averageCallDuration": {"$avg": "$calls.duration"}}}
    ]

    if not is_super_admin:
        pipeline.append({"$match": {"ownerName": userId}})

    result = collection.aggregate(pipeline)
    print("result", result)
    result = next(result, {"averageCallDuration": 0})
    return result["averageCallDuration"]

def get_matrix_details(id: str, userName: str):
    """
    Get detailed prospect data based on the metric ID.
    
    Args:
        id (str): The metric ID to filter by (calls-made, calls-connected, appointments, callbacks, ebooks, average-call-duration)
        userName (str): The username of the requesting user
        
    Returns:
        list: Filtered prospect data based on the metric ID
    """
    collection = get_prospects_collection()
    users_collection = get_users_collection()

    # Check if user is a super_admin
    user = users_collection.find_one({"name": userName})
    is_super_admin = user and user.get("role") == "super_admin"

    # Base query - will be modified based on the metric ID
    base_query = {}
    
    # Add owner filter if not a super_admin
    if not is_super_admin:
        base_query["ownerName"] = userName
    
    # Fields to return in the result
    projection = {
        "name": 1,
        "phoneNumber": 1,
        "businessName": 1,
        "email": 1,
        "status": 1,
        "ownerName": 1,
        "campaignName": 1,
        "scheduledCallDate": 1,
        "_id": 0
    }
    
    # Apply specific filters based on the metric ID
    if id == "calls-made":
        # All calls made (prospects with calls array)
        base_query["calls"] = {"$exists": True, "$ne": []}
        projection["calls"] = 1
        
    elif id == "calls-connected":
        # Connected calls (calls with status "ended")
        base_query["calls.status"] = "ended"
        projection["calls"] = 1
        
    elif id == "appointments":
        # Appointments booked
        base_query["appointment.appointmentInterest"] = True
        projection["appointment"] = 1
        
    elif id == "callbacks":
        # Callbacks scheduled (future callbacks)
        base_query["callBackDate"] = {"$exists": True}
        projection["callBackDate"] = 1
        projection["callBackTime"] = 1
        
    elif id == "ebooks":
        # Ebooks sent
        base_query["isEbook"] = True
        
    elif id == "average-call-duration":
        # For average call duration, we need to include call duration data
        base_query["calls.duration"] = {"$exists": True}
        projection["calls.duration"] = 1
    
    # Execute the query
    prospects = list(collection.find(base_query, projection))
    
    # Transform the result for better frontend consumption
    result = []
    for prospect in prospects:
        # Ensure all fields are present
        transformed_prospect = {
            "name": prospect.get("name", ""),
            "phoneNumber": prospect.get("phoneNumber", ""),
            "businessName": prospect.get("businessName", ""),
            "email": prospect.get("email", ""),
            "status": prospect.get("status", ""),
            "ownerName": prospect.get("ownerName", ""),
            "campaignName": prospect.get("campaignName", ""),
            "scheduledCallDate": prospect.get("scheduledCallDate", "")
        }
        
        # Add metric-specific data
        if id == "calls-made" or id == "calls-connected":
            # Include call details
            if "calls" in prospect:
                transformed_prospect["calls"] = prospect["calls"]
                
        elif id == "appointments":
            # Include appointment details
            if "appointment" in prospect:
                transformed_prospect["appointment"] = prospect["appointment"]
                transformed_prospect["appointment"]["meetingLink"] = prospect["appointment"].get("meetingLink", "")
                
        elif id == "callbacks":
            # Include callback details
            transformed_prospect["callBackDate"] = prospect.get("callBackDate", "")
            transformed_prospect["callBackTime"] = prospect.get("callBackTime", "")
            
        elif id == "average-call-duration":
            # Include call duration details
            if "calls" in prospect:
                durations = [call.get("duration", 0) for call in prospect["calls"] if "duration" in call]
                if durations:
                    transformed_prospect["averageCallDuration"] = sum(durations) / len(durations)
        
        result.append(transformed_prospect)
    
    return {
        "status": "success",
        "message": f"Details for {id} retrieved successfully",
        "data": result
    }

def get_call_back_schedule(userId: str):
    """Schedule the call back for the prospect."""
    collection = get_prospects_collection()
    users_collection = get_users_collection()

    # Check if user is a super_admin
    user = users_collection.find_one({"name": userId})
    is_super_admin = user and user.get("role") == "super_admin"

    # Build match stage
    match_stage = {"callBackDate": {"$exists": True}}

    # Only add ownerName if not outbound and not a super_admin
    if not is_super_admin:
        match_stage["ownerName"] = userId
    total_scheduled_callbacks = collection.aggregate([
        {"$match": match_stage},
        {"$count": "totalScheduledCallbacks"}
    ])
    print("total_scheduled_callbacks", total_scheduled_callbacks)
    result = next(total_scheduled_callbacks, {"totalScheduledCallbacks": 0})
    return result["totalScheduledCallbacks"]

def get_prospects_summary(user_id=None):
    """Retrieve a summary of prospects with phone number, name, status, and userId, filtered by user role."""
    collection = get_prospects_collection()
    users_collection = get_users_collection()
    query = {}
    if user_id:
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user and user.get("role") != "super_admin":
            # Filter by ownerName (user's name)
            query["ownerName"] = user["name"]
    # Add userId to projection if it exists in the collection
    
    # prospects_summary = collection.find(query, {"phoneNumber": 1, "name": 1, "businessName": 1, "ownerName": 1, "status": 1, "userId": 1, "_id": 0, "scheduledCallDate": 1})
    print("query", query)
    prospects_summary = list(collection.find(query, {
    "phoneNumber": 1,
    "name": 1,
    "businessName": 1,
    "ownerName": 1,
    "status": 1,
    "userId": 1,
    "campaignName": 1,
    "_id": 0,
    "scheduledCallDate": 1
}))
    # If userId is not present in the document, set it to None
    result = []
    for prospect in prospects_summary:
        if "userId" not in prospect:
            prospect["userId"] = None
        result.append(prospect)
    return result

def get_calendar_events(month=None, year=None, owner_name=None, user_role=None):
    """Retrieve calendar events for all prospects with picked_up status and appointment data in a single query.
    
    Args:
        month (int, optional): Month number (1-12) to filter events by
        year (int, optional): Year to filter events by
        owner_name (str, optional): Filter events by owner name
        user_role (str, optional): Filter events by user role (e.g., super_admin)
    
    Returns:
        list: Calendar events
    """

    print("owner_name", owner_name)
    print("month", month)
    print("year", year)
    print("user_role", user_role)
    from services.prospect_service import get_prospects_collection
    from datetime import datetime
    
    collection = get_prospects_collection()
    
    # Create the base query for picked_up prospects with appointment data
    query = {
        "status": {"$in": ["picked_up", "contacted"]},
        "appointment.appointmentDateTime": {"$ne": None}
    }
    
    # Add owner name filtering if provided
    # The owner_name is required now - we always want to filter by the current user
    if owner_name:
            query["ownerName"] = owner_name
    # If super_admin, do not filter by owner_name
    
    # Add date range filtering if month and year are provided
    if month is not None and year is not None:
        # Calculate start and end dates for the given month
        if month == 12:
            start_date = f"{year}-{month:02d}-01"
            end_date = f"{year+1}-01-01"
        else:
            start_date = f"{year}-{month:02d}-01"
            end_date = f"{year}-{month+1:02d}-01"
        
        # Add date range condition to the query using regex to match ISO date strings
        # This will match dates regardless of the time portion and timezone suffix
        query["appointment.appointmentDateTime"] = {
            "$regex": f"^{year}-{month:02d}-.*"
        }
    
    print("Final query:", query)
    
    # Find all prospects matching the query
    picked_up_prospects = collection.find(
        query if user_role != "super_admin" else {},
        {
            "phoneNumber": 1,
            "name": 1,
            "businessName": 1,
            "appointment": 1,
            "calls": 1,
            "ownerName": 1,
            "_id": 0
        }
    )
    
    calendar_events = []
    
    for prospect in picked_up_prospects:
        # Only include prospects with appointment data
        if prospect.get("appointment") and prospect["appointment"].get("appointmentDateTime"):
            # Format the appointment data into a calendar event
            try:
                # Get meeting link safely
                meeting_link = prospect["appointment"].get("meetingLink", "")
                
                calendar_event = {
                    "id": prospect["phoneNumber"],
                    "title": f"{prospect['name']} - {prospect.get('businessName', 'No Business')}",
                    "appointmentDateTime": prospect["appointment"]["appointmentDateTime"],
                    "resource": {
                        "id": prospect["phoneNumber"],
                        "prospectName": prospect["name"],
                        "prospectPhoneNumber": prospect["phoneNumber"],
                        "businessName": prospect.get("businessName"),
                        "appointmentDateTime": prospect["appointment"]["appointmentDateTime"],
                        "appointmentType": prospect["appointment"]["appointmentType"],
                        "notes": prospect.get("calls", [{}])[0].get("callSummary", "") if prospect.get("calls") else "",
                        "ownerName": prospect.get("ownerName", "Unknown User"),
                        "status": "scheduled",
                        "meetingLink": meeting_link
                    },
                    "meetingLink": meeting_link
                }
                calendar_events.append(calendar_event)
            except Exception as e:
                # Skip any events that can't be properly formatted
                print(f"Error formatting calendar event: {str(e)}")
                continue
    
    return calendar_events

def get_monthly_stats(month: int, year: int):
    """
    Get statistics for a specific month and year
    
    Args:
        month (int): Month number (1-12)
        year (int): Year (e.g., 2025)
        
    Returns:
        dict: Monthly statistics
    """
    collection = get_prospects_collection()
    
    # Calculate start and end dates for the month
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    # Base match condition for the date range
    date_match = {
        "$and": [
            {"createdAt.$date": {"$gte": start_date}},
            {"createdAt.$date": {"$lt": end_date}}
        ]
    }

    # Get total prospects created in the month
    total_prospects = collection.count_documents(date_match)

    # Get total calls made in the month
    calls_pipeline = [
        {"$unwind": "$calls"},
        {
            "$match": {
                "calls.timestamp": {
                    "$gte": start_date,
                    "$lt": end_date
                }
            }
        },
        {"$count": "total"}
    ]
    total_calls = next(collection.aggregate(calls_pipeline), {"total": 0}).get("total", 0)

    # Get connected calls in the month
    connected_calls_pipeline = [
        {"$unwind": "$calls"},
        {
            "$match": {
                "$and": [
                    {"calls.timestamp": {"$gte": start_date, "$lt": end_date}},
                    {"calls.status": "ended"}
                ]
            }
        },
        {"$count": "total"}
    ]
    connected_calls = next(collection.aggregate(connected_calls_pipeline), {"total": 0}).get("total", 0)

    # Get appointments booked in the month
    appointments_match = {
        **date_match,
        "appointment.appointmentInterest": True
    }
    appointments_booked = collection.count_documents(appointments_match)

    # Get ebooks sent in the month
    ebooks_match = {
        **date_match,
        "isEbook": True
    }
    ebooks_sent = collection.count_documents(ebooks_match)

    # Get callbacks scheduled in the month
    callbacks_match = {
        "callBackDate": {"$gte": start_date, "$lt": end_date}
    }
    callbacks_scheduled = collection.count_documents(callbacks_match)

    return {
        "status": "success",
        "data": {
            "total_prospects": total_prospects,
            "total_calls": total_calls,
            "connected_calls": connected_calls,
            "appointments_booked": appointments_booked,
            "ebooks_sent": ebooks_sent,
            "callbacks_scheduled": callbacks_scheduled,
        }
    }
