import { DUMMY_SHIFT_TEMPLATES, ShiftTemplate } from './shift-templates.dummy';
import { DUMMY_SHIFT_TYPES, ShiftType } from './shift-types.dummy';
import { DUMMY_USERS, User } from './users.dummy';

export interface Shift {
  id: string; // Unique identifier for the shift
  shiftDate: Date; // Date of the shift
  user: User;
  job: string; // User assigned to the shift
  shiftTypeId: ShiftType;
  startTime: string;
  endTime: string;
  lunchStartTime?: string; // Optional lunch start time
  lunchEndTime?: string; // Optional lunch end time
  workingHours: number; // Total working hours for the shift
  shiftTemplateId: ShiftTemplate; // Optional reference to a shift template
}

export const DUMMY_SHIFTS: Shift[] = [
  {
    id: '1',
    shiftDate: new Date('2023-10-01'),
    user: DUMMY_USERS[0],
    job: 'Service Desk Analyst',
    shiftTypeId: DUMMY_SHIFT_TYPES[0],
    startTime: DUMMY_SHIFT_TEMPLATES[0].startTime,
    endTime: DUMMY_SHIFT_TEMPLATES[0].endTime,
    lunchStartTime: DUMMY_SHIFT_TEMPLATES[0].lunchStartTime,
    lunchEndTime: DUMMY_SHIFT_TEMPLATES[0].lunchEndTime,
    workingHours: 7.5,
    shiftTemplateId: DUMMY_SHIFT_TEMPLATES[0], // Live Shift
  },
];
