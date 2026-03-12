export interface Team {
  id: number;
  name: string;
  teamColor?: string; // Optional property for team color
}

export const DUMMY_TEAMS: Team[] = [
  { id: 1, name: 'Red Team', teamColor: '#4CAF50' },
  { id: 2, name: 'Green Team', teamColor: '#2196B3' },
  { id: 3, name: 'Yellow Team', teamColor: '#FF9800' },
];
