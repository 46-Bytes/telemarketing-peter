/**
 * Timezone utility functions for Brisbane, Australia timezone handling.
 * All functions use Australia/Brisbane timezone consistently across the frontend.
 */

/**
 * Get current date in Brisbane timezone in YYYY-MM-DD format
 * This is used for date input validation to prevent selecting past dates
 */
export const getBrisbaneDate = (): string => {
  const now = new Date();
  const brisbaneTime = new Date(now.toLocaleString("en-US", { timeZone: "Australia/Brisbane" }));
  return brisbaneTime.toISOString().split('T')[0];
};

/**
 * Get current time in Brisbane timezone in HH:MM format
 */
export const getBrisbaneTime = (): string => {
  const now = new Date();
  const brisbaneTime = new Date(now.toLocaleString("en-US", { timeZone: "Australia/Brisbane" }));
  return brisbaneTime.toTimeString().split(' ')[0].substring(0, 5);
};

/**
 * Get current datetime in Brisbane timezone
 */
export const getBrisbaneDateTime = (): Date => {
  const now = new Date();
  return new Date(now.toLocaleString("en-US", { timeZone: "Australia/Brisbane" }));
};

/**
 * Format a date string to Brisbane timezone for display
 */
export const formatBrisbaneDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-AU', { 
      timeZone: 'Australia/Brisbane',
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  } catch (e) {
    console.error('Error formatting date:', e);
    return dateString;
  }
};

/**
 * Format a datetime string to Brisbane timezone for display
 */
export const formatBrisbaneDateTime = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleString('en-AU', { 
      timeZone: 'Australia/Brisbane',
      year: 'numeric', 
      month: 'long', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    console.error('Error formatting datetime:', e);
    return dateString;
  }
};

/**
 * Check if current time is within business hours (10 AM to 7 PM) in Brisbane timezone
 */
export const isWithinBusinessHours = (): boolean => {
  const brisbaneTime = getBrisbaneDateTime();
  const hour = brisbaneTime.getHours();
  return hour >= 10 && hour < 19;
};

/**
 * Get timezone information for debugging
 */
export const getBrisbaneTimezoneInfo = () => {
  const brisbaneTime = getBrisbaneDateTime();
  return {
    brisbaneTime: brisbaneTime.toISOString(),
    brisbaneDate: getBrisbaneDate(),
    brisbaneTimeOnly: getBrisbaneTime(),
    timezone: 'Australia/Brisbane',
    isWithinBusinessHours: isWithinBusinessHours()
  };
};
