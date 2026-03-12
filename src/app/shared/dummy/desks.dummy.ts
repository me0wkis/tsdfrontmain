export interface Desk {
  id: number;
  deskNumber: string; // Unique identifier for the desk
}

export const DUMMY_DESKS: Desk[] = [
  { id: 1, deskNumber: '2.041' },
  { id: 2, deskNumber: '2.042' },
  { id: 3, deskNumber: '2.043' },
  { id: 4, deskNumber: '2.044' },
  { id: 5, deskNumber: '2.045' },
];
