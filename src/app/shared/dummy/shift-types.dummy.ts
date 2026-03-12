export interface ShiftType {
  id: number;
  name: string;
  code: string;
  color?: string;
  isWorking: boolean;
  isActive: boolean;
  description?: string;
  icon?: string;
}

export const DUMMY_SHIFT_TYPES: ShiftType[] = [
  {
    id: 1,
    name: 'Live Shift',
    code: 'L',
    color: '#FF9800',
    isWorking: true,
    isActive: true,
    description: 'Live shift',
    icon: 'sunrise',
  },
  {
    id: 2,
    name: 'Combined Shift',
    code: 'C',
    color: '#2196B3',
    isWorking: true,
    isActive: true,
    description: 'Combined shift',
  },
  {
    id: 3,
    name: 'Email Shift',
    code: 'E',
    color: '#9C27B0',
    isWorking: true,
    isActive: true,
    description: 'Email shift',
  },
  {
    id: 4,
    name: 'Ordinary Shift',
    code: 'M',
    color: '#673AB7',
    isWorking: true,
    isActive: true,
    description: 'Ordinary shift',
  },
  {
    id: 5,
    name: 'Backlog Cleaner Shift',
    code: 'B',
    color: '#4CAF50',
    isWorking: true,
    isActive: true,
    description: 'Backlog cleaner shift',
  },
  {
    id: 6,
    name: 'Holiday Shift',
    code: 'H',
    color: '#F44336',
    isWorking: true,
    isActive: true,
    description: 'Holiday shift',
  },
];
