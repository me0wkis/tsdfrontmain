import { DUMMY_SHIFT_TYPES, ShiftType } from './shift-types.dummy';

export interface ShiftTemplate {
  id: string;
  code: string;
  isFixedTime: boolean;
  startTime: string;
  endTime: string;
  lunchStartTime: string;
  lunchEndTime: string;
  shiftTypeId: ShiftType; // Reference to ShiftType
  allowedRoles: string[];
  isOffice: boolean;
  isActive: boolean;
  icon?: string;
  description?: string;
}

export const DUMMY_SHIFT_TEMPLATES: ShiftTemplate[] = [
  {
    id: '1',
    code: '2',
    isFixedTime: true,
    startTime: '08:00',
    endTime: '17:00',
    lunchStartTime: '12:00',
    lunchEndTime: '13:00',
    shiftTypeId: DUMMY_SHIFT_TYPES[0], // Live Shift
    allowedRoles: ['Service Desk Analyst', 'supervisor'],
    isOffice: true,
    isActive: true,
    icon: 'work',
    description:
      'Standard office hours shift from 8 AM to 5 PM with a lunch break.',
  },
  {
    id: '2',
    code: '3',
    isFixedTime: true,
    startTime: '09:00',
    endTime: '18:00',
    lunchStartTime: '13:00',
    lunchEndTime: '14:00',
    shiftTypeId: DUMMY_SHIFT_TYPES[0], // Combined Shift
    allowedRoles: ['Service Desk Analyst', 'supervisor'],
    isOffice: true,
    isActive: true,
    description:
      'Flexible office hours shift from 9 AM to 6 PM with a lunch break.',
  },
  {
    id: '3',
    code: '4',
    isFixedTime: true,
    startTime: '10:00',
    endTime: '19:00',
    lunchStartTime: '14:00',
    lunchEndTime: '15:00',
    shiftTypeId: DUMMY_SHIFT_TYPES[0], // Night Shift
    allowedRoles: ['Service Desk Analyst', 'supervisor'],
    isOffice: true,
    isActive: true,
    description: 'Shift from 10 PM to 7 AM with a lunch break.',
  },
  {
    id: '4',
    code: '5',
    isFixedTime: false,
    startTime: '11:00',
    endTime: '19:00',
    lunchStartTime: '15:00',
    lunchEndTime: '16:00',
    shiftTypeId: DUMMY_SHIFT_TYPES[0], // Ordinary Shift
    allowedRoles: ['Service Desk Analyst'],
    isOffice: true,
    isActive: true,
    description: 'Ordinary shift with flexible start and end times.',
  },
  {
    id: '5',
    code: '6',
    isFixedTime: true,
    startTime: '12:00',
    endTime: '20:00',
    lunchStartTime: '16:00',
    lunchEndTime: '17:00',
    shiftTypeId: DUMMY_SHIFT_TYPES[0], // Backlog Cleaner Shift
    allowedRoles: ['Service Desk Analyst'],
    isOffice: true,
    isActive: true,
    description: 'Shift from 12 PM to 8 PM with a lunch break.',
  },
  {
    id: '6',
    code: '7',
    isFixedTime: true,
    startTime: '13:00',
    endTime: '21:00',
    lunchStartTime: '17:00',
    lunchEndTime: '18:00',
    shiftTypeId: DUMMY_SHIFT_TYPES[0], // Holiday Shift
    allowedRoles: ['Service Desk Analyst'],
    isOffice: true,
    isActive: true,
    description: 'Holiday shift from 1 PM to 9 PM with a lunch break.',
  },
  {
    id: '7',
    code: '8',
    isFixedTime: true,
    startTime: '14:00',
    endTime: '22:00',
    lunchStartTime: '18:00',
    lunchEndTime: '19:00',
    shiftTypeId: DUMMY_SHIFT_TYPES[0], // Night Shift
    allowedRoles: ['Service Desk Analyst'],
    isOffice: true,
    isActive: true,
    description: 'Night shift from 2 PM to 10 PM with a lunch break.',
  },
];
