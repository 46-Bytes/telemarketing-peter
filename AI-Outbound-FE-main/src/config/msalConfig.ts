import { Configuration, PopupRequest } from "@azure/msal-browser";

export const msalConfig: Configuration = {
    auth: {
        clientId: import.meta.env.VITE_MICROSOFT_CLIENT_ID || "",
        authority: `https://login.microsoftonline.com/${import.meta.env.VITE_MICROSOFT_TENANT_ID}`,
        // authority: "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        redirectUri: window.location.origin,
    },
    cache: {
        cacheLocation: "sessionStorage",
        storeAuthStateInCookie: false,
    }
};

export const loginRequest: PopupRequest = {
    scopes: [
        "User.Read",
        "Calendars.ReadWrite",
        "Mail.Send",
        "offline_access"
    ]
};

export const graphConfig = {
    graphMeEndpoint: "https://graph.microsoft.com/v1.0/me",
    graphCalendarEndpoint: "https://graph.microsoft.com/v1.0/me/calendar/events"
}; 