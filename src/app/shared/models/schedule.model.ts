export interface ScheduleResponse {
  year: number;
  month: number;
  monthName: string;
  teams: TeamName[];
}

export interface TeamName {
  teamName: string;
  users: UserSchedule[];
}

export interface UserSchedule {
  id: number;
  fullName: string;
  shifts: Shift[];
}

export interface Shift {
  id: number;
  shiftDate: string; // format: YYYY-MM-DD
  jobTitle: string | null;
  shortCode: string;
  startTime: string; // format: 'HH:MM:SS'
  endTime: string; // format: 'HH:MM:SS'
  lunchStartTime: string; // format: 'HH:MM:SS'
  lunchEndTime: string; // format: 'HH:MM:SS'
  workHours: number;
}
