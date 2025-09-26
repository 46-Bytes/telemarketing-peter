import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  format,
  parseISO,
  addHours,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameDay,
} from "date-fns";
import { userApi } from "../api/api";
import { CalendarEvent } from "../types/appointment";
import { useAuth } from "../contexts/AuthContext";
import { useMicrosoftGraph } from "../hooks/useMicrosoftGraph";
import ApiKeyRequired from "../components/ApiKeyRequired";
import { CalendarEventResponse } from "../types/calendar";

// Helper function to format dates in Indian format
const formatIndianDate = (date: Date): string => {
  return format(date, "dd/MM/yyyy");
};

// Helper function to format time in Indian format (12-hour with AM/PM)
const formatIndianTime = (date: Date): string => {
  return format(date, "hh:mm a");
};

// Helper function to format date and time together in Indian format
const formatIndianDateTime = (date: Date): string => {
  return `${formatIndianDate(date)} ${formatIndianTime(date)}`;
};

// interface Prospect {
//   name: string;
//   phoneNumber: string;
//   status: string;
//   businessName?: string;
//   scheduledCallDate: string | null;
//   appointment?: {
//     appointmentInterest: boolean | null;
//     appointmentDateTime: string | null;
//   };
// }

const Calendar: React.FC = () => {
  const { user } = useAuth();
  const { checkAndRefreshToken } = useMicrosoftGraph();
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(
    null
  );
  const [isDetailModalOpen, setIsDetailModalOpen] = useState<boolean>(false);
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());
  const [error, setError] = useState<string | null>(null);
  const [selectedOwner] = useState<string | null>(null);
  const [, setAllOwners] = useState<string[]>([]);

  // Add a ref to track if data has already been fetched
  const dataFetchedRef = useRef<boolean>(false);

  const fetchCalendarEvents = useCallback(async () => {
    // Skip if already fetched data unless explicitly refreshing
    if (dataFetchedRef.current && !isRefreshing) {
      return;
    }

    setIsLoading(true);
    try {
      // First, ensure Microsoft token is valid before fetching calendar data
      try {
        console.log(
          "Ensuring Microsoft token is valid before fetching calendar events..."
        );
        await checkAndRefreshToken();
        setError(null);
      } catch (tokenError) {
        console.error("Error refreshing Microsoft token:", tokenError);
        setError(
          "Microsoft authentication error. Please reconnect your Microsoft account."
        );
        setIsLoading(false);
        setIsRefreshing(false);
        return;
      }

      // Get the month and year from the current month state
      const month = currentMonth.getMonth() + 1; // JavaScript months are 0-indexed
      const year = currentMonth.getFullYear();

      // Get the user's name for filtering - if no owner is selected, use current user
      // If a specific owner is selected, use that instead
      const ownerName = selectedOwner || user?.name;

      // Fetch calendar events for the specific month and owner
      const response = await userApi.getCalendarEvents(month, year, ownerName, user?.role);
      console.log("Calendar data fetched:", response);
      const calendarEvents: CalendarEvent[] = [];

      // Process the events
      response.calendar_events.forEach((event: CalendarEventResponse) => {
        // Check if event has valid date before processing
        if (!event.appointmentDateTime) {
          console.warn("Event missing appointmentDateTime:", event);
          return; // Skip this event
        }

        try {
          const startDate = parseISO(event.appointmentDateTime);
          const endDate = addHours(startDate, 1); // Assume appointments last 1 hour

          // Log the event data to debug meeting link information
          console.log("Calendar event:", {
            id: event.id,
            title: event.title,
            meetingLink: event.meetingLink,
            resource: event.resource,
          });

          // Check for meeting link in various possible locations in the response
          // Backend might send the link in different properties based on its structure
          const meetingLink =
            // Check direct property
            event.meetingLink ||
            // Check in resource object
            (event.resource && event.resource.meetingLink) ||
            // Check in appointment object if it exists
            (event.appointment && event.appointment.meetingLink) ||
            // Check custom fields or other locations
            event.meeting_link ||
            (event.resource && event.resource.meeting_link) ||
            null;

          calendarEvents.push({
            id: event.id,
            title: event.title,
            start: startDate,
            end: endDate,
            resource: {
              id: event.resource?.id ?? "",
              meetingLink: meetingLink || "",
              prospectName: event.resource?.prospectName ?? "",
              prospectPhoneNumber: event.resource?.prospectPhoneNumber ?? "",
              businessName: event.resource?.businessName ?? "",
              appointmentDateTime: event.resource?.appointmentDateTime ?? "",
              notes: event.resource?.notes ?? "",
              ownerName: event.resource?.ownerName ?? "",
              status: (event.resource?.status ?? "scheduled") as
                | "scheduled"
                | "completed"
                | "cancelled"
                | "no-show",
              appointmentType: (event.resource?.appointmentType ??
                "selling") as "selling" | "advisory",
            },
          });
        } catch (err) {
          console.error("Error processing calendar event:", err, event);
        }
      });

      setEvents(calendarEvents);

      // Extract unique owner names from the events for the filter dropdown
      const owners = response.calendar_events
        .map(
          (event: CalendarEventResponse) =>
            event.resource?.ownerName || event?.ownerName
        )
        .filter((name: string | undefined): name is string => !!name);

      // Use explicit type assertion for the array of unique owners
      const uniqueOwnersSet = new Set<string>(owners);
      const uniqueOwners = Array.from(uniqueOwnersSet).sort() as string[];
      setAllOwners(uniqueOwners);
      setLastRefreshed(new Date());

      // Mark data as fetched unless we're manually refreshing
      if (!isRefreshing) {
        dataFetchedRef.current = true;
      }
    } catch (err) {
      console.error("Error fetching calendar events:", err);
      setEvents([]);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [currentMonth, user, checkAndRefreshToken, selectedOwner, isRefreshing]);

  // Initial data loading
  useEffect(() => {
    fetchCalendarEvents();
    // Don't include fetchCalendarEvents in dependency array to prevent continuous refreshing
  }, []);

  // Only refetch when currentMonth or selectedOwner changes
  useEffect(() => {
    // Skip the initial render since we already fetch in the mount effect
    if (dataFetchedRef.current) {
      dataFetchedRef.current = false; // Reset so we'll fetch on this change
      fetchCalendarEvents();
    }
  }, [currentMonth, selectedOwner]);

  // Remove auto-refresh interval that causes continuous API calls
  // useEffect(() => {
  //   const refreshInterval = setInterval(() => {
  //     console.log("Auto-refreshing calendar data...");
  //     fetchCalendarEvents();
  //   }, 30000);
  //
  //   return () => clearInterval(refreshInterval);
  // }, [fetchCalendarEvents]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchCalendarEvents();
  };

  const handleEventClick = (event: CalendarEvent) => {
    console.log("Event clicked:", {
      id: event.id,
      title: event.title,
      meetingLink: event.resource?.meetingLink,
      hasResource: !!event.resource,
      resourceKeys: event.resource ? Object.keys(event.resource) : [],
      resource: event.resource,
    });
    setSelectedEvent(event);
    setIsDetailModalOpen(true);
  };

  const handleOpenMeetingLink = (meetingLink: string) => {
    if (!meetingLink) {
      console.error("Meeting link is empty or invalid");
      return;
    }

    try {
      // Ensure the link has a proper protocol
      let formattedLink = meetingLink.trim();

      // Check if it's a valid URL format
      if (!formattedLink.match(/^(https?:\/\/|teams:\/\/)/i)) {
        // If it's a Microsoft Teams meeting ID or code only
        if (formattedLink.match(/^[a-zA-Z0-9_-]+$/)) {
          formattedLink = `https://teams.microsoft.com/l/meetup-join/${formattedLink}`;
        }
        // General case - add https if no protocol
        else if (
          !formattedLink.startsWith("http://") &&
          !formattedLink.startsWith("https://")
        ) {
          formattedLink = "https://" + formattedLink;
        }
      }

      // Log the formatted link for debugging
      console.log("Opening meeting link:", formattedLink);

      // Simply try to open the URL - modern browsers handle popup blocking on their own
      const windowRef = window.open(formattedLink, "_blank");

      // Only show a message if we can definitely tell it failed
      if (windowRef === null) {
        console.warn("Meeting link may have been blocked by popup blocker");
        // Optional: Provide instructions to the user about popup blockers
        alert(
          "Your browser may have blocked the meeting link. Please check your popup blocker settings."
        );
      }
    } catch (error) {
      console.error("Error opening meeting link:", error);
      alert(
        "There was an error opening the meeting link. Please try again or contact support."
      );
    }
  };

  const handleCloseModal = () => {
    setIsDetailModalOpen(false);
    setSelectedEvent(null);
  };

  const getStatusColor = (status: string) => {
    const statusColors = {
      scheduled: "bg-blue-100 text-blue-800 border-blue-300",
      completed: "bg-green-100 text-green-800 border-green-300",
      cancelled: "bg-red-100 text-red-800 border-red-300",
      "no-show": "bg-orange-100 text-orange-800 border-orange-300",
      picked_up: "bg-green-100 text-green-800 border-green-300",
    };

    return (
      statusColors[status.toLowerCase() as keyof typeof statusColors] ||
      "bg-gray-100 text-gray-800 border-gray-300"
    );
  };

  const renderCalendarHeader = () => {
    return (
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-xl font-semibold">
            {format(currentMonth, "MMMM yyyy")}
          </h2>
          <p className="text-xs text-gray-500">
            Last updated: {format(lastRefreshed, "h:mm:ss a")}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() =>
              setCurrentMonth(
                (prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1)
              )
            }
            className="px-3 py-1 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Previous
          </button>
          <button
            onClick={() => setCurrentMonth(new Date())}
            className="px-3 py-1 bg-blue-100 rounded-lg hover:bg-blue-200"
          >
            Today
          </button>
          <button
            onClick={() =>
              setCurrentMonth(
                (prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1)
              )
            }
            className="px-3 py-1 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            Next
          </button>
          {/* <select
            value={selectedOwner || ''}
            onChange={(e) => setSelectedOwner(e.target.value === '' ? null : e.target.value)}
            className="px-3 py-1 bg-gray-100 rounded-lg hover:bg-gray-200 text-sm"
          >
            <option value="">All Owners</option>
            {allOwners.map((owner) => (
              <option key={owner} value={owner}>{owner}</option>
            ))}
          </select> */}
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className={`px-3 py-1 rounded-lg flex items-center ${
              isRefreshing
                ? "bg-gray-100 text-gray-400"
                : "bg-green-100 hover:bg-green-200 text-green-800"
            }`}
          >
            {isRefreshing ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-400"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Refreshing...
              </>
            ) : (
              <>
                <svg
                  className="h-4 w-4 mr-1"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                Refresh
              </>
            )}
          </button>
        </div>
      </div>
    );
  };

  const renderCalendarDays = () => {
    const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

    return (
      <div className="grid grid-cols-7 gap-1 mb-1">
        {days.map((day) => (
          <div
            key={day}
            className="text-center py-2 font-semibold text-gray-600 bg-gray-100 rounded-lg"
          >
            {day}
          </div>
        ))}
      </div>
    );
  };

  const renderCalendarCells = () => {
    const monthStart = startOfMonth(currentMonth);
    const monthEnd = endOfMonth(monthStart);
    const startDate = new Date(monthStart);
    startDate.setDate(startDate.getDate() - startDate.getDay());
    const endDate = new Date(monthEnd);
    endDate.setDate(endDate.getDate() + (6 - endDate.getDay()));

    const dateRange = eachDayOfInterval({ start: startDate, end: endDate });

    return (
      <div className="grid grid-cols-7 gap-1">
        {dateRange.map((date, i) => {
          const isCurrentMonth = date.getMonth() === currentMonth.getMonth();
          const isToday = isSameDay(date, new Date());
          const isSelected = selectedDate && isSameDay(date, selectedDate);

          // Find events for this day
          const dayEvents = events.filter((event) =>
            isSameDay(event.start, date)
          );

          return (
            <div
              key={i}
              onClick={() => setSelectedDate(date)}
              className={`min-h-[100px] p-2 rounded-lg border ${
                isCurrentMonth ? "bg-white" : "bg-gray-50"
              } ${isToday ? "border-blue-400" : "border-gray-200"} ${
                isSelected ? "ring-2 ring-blue-500" : ""
              } hover:border-blue-300 cursor-pointer transition-colors`}
            >
              <div
                className={`text-right font-semibold ${
                  isCurrentMonth ? "text-gray-700" : "text-gray-400"
                } ${isToday ? "text-blue-600" : ""}`}
              >
                {format(date, "d")}
              </div>
              <div className="mt-1 space-y-1">
                {dayEvents.slice(0, 3).map((event) => (
                  <div
                    key={event.id}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEventClick(event);
                    }}
                    className="text-xs p-1 rounded bg-blue-50 border-l-4 border-blue-400 truncate hover:bg-blue-100"
                  >
                    {formatIndianTime(event.start)} - {event.title}
                    {event.resource?.meetingLink && (
                      <span className="ml-1 inline-flex items-center">
                        <svg
                          className="h-3 w-3 text-blue-600"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"
                          />
                        </svg>
                      </span>
                    )}
                  </div>
                ))}
                {dayEvents.length > 3 && (
                  <div className="text-xs text-gray-500 text-center">
                    +{dayEvents.length - 3} more
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // Calendar content to render inside MicrosoftAuthRequired
  const calendarContent = () => {
    if (isLoading) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div
          className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4"
          role="alert"
        >
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      );
    }

    return (
      <>
        {/* Calendar UI */}
        <div className="bg-white rounded-lg overflow-hidden p-6">
          {renderCalendarHeader()}
          {renderCalendarDays()}
          {renderCalendarCells()}
        </div>

        {/* Event detail modal */}
        {isDetailModalOpen && selectedEvent && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-[150]">
            {/* Modal content */}
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
              <div className="px-6 py-4 border-b">
                <h3 className="text-lg font-semibold">{selectedEvent.title}</h3>
              </div>
              <div className="p-6">
                <div className="space-y-3">
                  <div>
                    <p className="text-sm font-medium text-gray-500">
                      Date and Time
                    </p>
                    <p className="text-gray-900">
                      {formatIndianDateTime(selectedEvent.start)}
                    </p>
                  </div>
                  {selectedEvent.resource?.prospectPhoneNumber && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">
                        Phone Number
                      </p>
                      <p className="text-gray-900">
                        {selectedEvent.resource.prospectPhoneNumber}
                      </p>
                    </div>
                  )}
                  {selectedEvent.resource?.prospectName && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">
                        Prospect
                      </p>
                      <p className="text-gray-900">
                        {selectedEvent.resource.prospectName}
                      </p>
                    </div>
                  )}
                  {selectedEvent.resource?.businessName && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">
                        Business
                      </p>
                      <p className="text-gray-900">
                        {selectedEvent.resource.businessName}
                      </p>
                    </div>
                  )}
                  {selectedEvent.resource?.ownerName && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Owner</p>
                      <p className="text-gray-900">
                        {selectedEvent.resource.ownerName}
                      </p>
                    </div>
                  )}
                  {selectedEvent.resource?.status && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">
                        Status
                      </p>
                      <span
                        className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(
                          selectedEvent.resource.status
                        )}`}
                      >
                        {selectedEvent.resource.status.toUpperCase()}
                      </span>
                    </div>
                  )}
                  {selectedEvent.resource?.appointmentType && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">
                        Appointment Type
                      </p>
                      <p className="text-gray-900 capitalize">
                        {selectedEvent.resource.appointmentType}
                      </p>
                    </div>
                  )}
                  {selectedEvent.resource?.meetingLink && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">
                        Meeting Link
                      </p>
                      <button
                        onClick={() =>
                          handleOpenMeetingLink(
                            selectedEvent.resource?.meetingLink || ""
                          )
                        }
                        className="mt-1 inline-flex items-center px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                      >
                        <svg
                          className="h-4 w-4 mr-1"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                          />
                        </svg>
                        Join Meeting
                      </button>
                    </div>
                  )}
                  {selectedEvent.resource?.notes && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">Notes</p>
                      <p className="text-gray-900">
                        {selectedEvent.resource.notes}
                      </p>
                    </div>
                  )}
                </div>
              </div>
              <div className="px-6 py-3 bg-gray-50 flex justify-end">
                <button
                  onClick={handleCloseModal}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </>
    );
  };

  return user?.role === "super_admin" ? (
    calendarContent()
  ) : (
    <ApiKeyRequired
      pageTitle="API Key Required"
      pageDescription="Enter your API key to access campaign details."
    >
      {calendarContent()}
    </ApiKeyRequired>
  );
};

export default Calendar;
