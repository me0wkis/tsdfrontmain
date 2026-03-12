export interface ShiftsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Shifts[];
}

export interface Shifts {
  id: number;
  user: string;
  shiftDate: string;
  jobTitle: string;
  shiftType: string;
  startTime: string;
  endTime: string;
  lunchStartTime: string;
  lunchEndTime: string;
  workHours: string;
  shiftTemplate: string;
  createdBy: string;
  isFixedTime: boolean;
}

export interface ShiftTypes {
  id: number;
  name: string;
  code: string;
  isWorkShift: boolean;
}

export interface ShiftTemplates {
  id: number;
  code: string;
  description: string;
  isFixedTime: boolean;
  startTime: string;
  endTime: string;
  lunchStartTime: string;
  lunchEndTime: string;
  shiftType: number;
  icon: string;
  allowedRoles: string;
  isActive: boolean;
  isOffice: boolean;
}

export interface ShiftTemplateRequest {
  code: string;
  description: string;
  isFixedTime: boolean;
  startTime: string;
  endTime: string;
  lunchStartTime: string;
  lunchEndTime: string;
  shiftType: number;
  icon: string;
  allowedRoles: string;
  isActive: boolean;
  isOffice: boolean;
}

export interface ShiftTypeRequest {
  name: string;
  code: string;
  isWorkShift: boolean;
}

export interface ShiftRequest {
  user: string;
  shiftDate: string;
  jobTitle: string;
  shiftType: string;
  startTime: string;
  endTime: string;
  lunchStartTime: string;
  lunchEndTime: string;
  shiftTemplate: string;
  createdBy: string;
}
