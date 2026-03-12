export interface CalendarAnomalyDTO {
  id: number;
  date: string; // формат 'YYYY-MM-DD'
  name: string;
  type: string; // например, 'Holiday'
}

export interface AnomaliesResponseDTO {
  year: number;
  month: number;
  anomalies: CalendarAnomalyDTO[];
}
