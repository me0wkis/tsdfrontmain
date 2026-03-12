export interface UsersResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: User[];
}

export interface User {
  id: number;
  alias: string;
  firstName: string;
  secondName: string;
  jobTitle: string;
  groupName: string;
  hiringDate: string;
  supervisorName: string;
  email: string;
  phoneNumber: string;
  desk: number;
  team: number;
  avatarUrl: string | null;
  isActive: boolean;
}

export interface UserRequest {
  alias: string;
  firstName: string;
  secondName: string;
  jobTitle: string;
  groupName: string;
  hiringDate: string;
  supervisorName: string;
  email: string;
  phoneNumber: string;
  desk: number;
  team: number;
  avatarUrl: string | null;
  isActive: boolean;
}
