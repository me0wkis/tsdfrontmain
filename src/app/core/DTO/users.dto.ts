export interface UsersResponsePaginatedDTO {
  count: number;
  next: string | null;
  previous: string | null;
  results: UserDTO[];
}

export interface UserDTO {
  id: number;
  alias: string;
  first_name: string;
  second_name: string;
  job_title: string;
  group_name: string;
  hiring_date: string;
  supervisor_name: string;
  email: string;
  phone_number: string;
  desk: number;
  team: number;
  avatar_url: string | null;
  is_active: number; // 0 or 1
}

export interface UserRequestDTO {
  alias: string;
  first_name: string;
  second_name: string;
  job_title: string;
  group_name: string;
  hiring_date: string;
  supervisor_name: string;
  email: string;
  phone_number: string;
  desk: number;
  team: number;
  avatar_url: string | null;
  is_active: number; // 0 or 1
}
