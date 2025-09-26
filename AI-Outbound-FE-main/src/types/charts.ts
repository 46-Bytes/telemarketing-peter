export interface ChartFilter {
  month: number;
  year: number;
}

export interface ChartDataPoint {
  x: string;
  y: number;
}

export interface ChartSeries {
  name: string;
  data: ChartDataPoint[];
  color: string;
}

export interface DailyStats {
  date: string;
  calls_made: number;
  calls_connected: number;
  appointments_booked: number;
  callbacks_scheduled: number;
  ebooks_sent: number;
}

export interface ChartDataResponse {
  data: DailyStats[];
} 