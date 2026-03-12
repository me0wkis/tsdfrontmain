export interface LoginRequestDTO {
  username: string;
  password: string;
}

export interface LoginResponseDTO {
  token: string;
  user: UserAuthDTO;
}

export interface UserAuthDTO {
  id: number;
  username: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  role?: string;
}

export interface AuthMeResponseDTO {
  authenticated: boolean;
  user?: UserAuthDTO;
}
