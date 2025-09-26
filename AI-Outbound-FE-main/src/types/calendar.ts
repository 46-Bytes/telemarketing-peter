export type CalendarEventResponse = {
    id: string;
    title: string;
    appointmentDateTime: string;
    ownerName?: string;
    meetingLink?: string | null;
    resource?: {
      id?: string;
      prospectName: string;
      prospectPhoneNumber: string;
      businessName?: string;
      appointmentDateTime: string;
      notes?: string;
      ownerName?: string;
      status: string;
      meetingLink?: string | null;
      appointmentType?: string;
      meeting_link?: string;
    };
    meeting_link?: string;
    appointment?: {
      meetingLink?: string | null;
    };
  };
