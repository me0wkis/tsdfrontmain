export interface CalendarAnomaly {
  id: number;
  date: string; // формат 'YYYY-MM-DD'
  name: string;
  type: string; // например, 'Holiday'
}

export interface AnomaliesResponse {
  year: number;
  month: number;
  anomalies: CalendarAnomaly[];
}
