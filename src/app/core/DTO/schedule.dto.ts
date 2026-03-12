// Данные с SCHEDULE эндпоинта API

export interface ScheduleResponseDTO {
  year: number;
  month: number;
  month_name: string;
  schedule: TeamNameDTO[];
}

export interface TeamNameDTO {
  team_name: string;
  users: UserScheduleDTO[];
}

export interface UserScheduleDTO {
  id: number;
  full_name: string;
  shifts: UserShiftsDTO[];
}

export interface UserShiftsDTO {
  id: number;
  shift_date: string; // format: YYYY-MM-DD
  job_title: string | null;
  short_code: string;
  start_time: string; // format: 'HH:MM:SS'
  end_time: string; // format: 'HH:MM:SS'
  lunch_start_time: string; // format: 'HH:MM:SS'
  lunch_end_time: string; // format: 'HH:MM:SS'
  work_hours: string; // format: '8.00'
}
