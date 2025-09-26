export interface Appointment {
  id: string;
  prospectName: string;
  prospectPhoneNumber: string;
  businessName?: string;
  appointmentDateTime: string;
  notes?: string;
  ownerName?: string;
  status: 'scheduled' | 'completed' | 'cancelled' | 'no-show';
  appointmentType?: 'selling' | 'advisory';
  meetingLink?: string;
}

export interface CalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  resource?: Appointment;
} 