import { MsalProvider } from "@azure/msal-react";
import { PublicClientApplication } from "@azure/msal-browser";
import { msalConfig } from "../config/msalConfig";
import { ReactNode } from "react";

const msalInstance = new PublicClientApplication(msalConfig);

interface Props {
    children: ReactNode;
}

export const MicrosoftAuthProvider = ({ children }: Props) => {
    return (
        <MsalProvider instance={msalInstance}>
            {children}
        </MsalProvider>
    );
}; 