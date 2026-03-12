import { inject, Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_BASE_URL, API_ENDPOINTS } from '@core/constants/api.constants';
import { User, UsersResponse } from '@shared/models/users.model';
import { UserDTO, UsersResponsePaginatedDTO } from '@core/DTO/users.dto';
import { MapperUtil } from '@core/utils/mapper.util';

export interface UsersQueryParams {
  limit?: number;
  offset?: number;
  sort?: string;
}

@Injectable({
  providedIn: 'root',
})
export class UsersService {
  private http = inject(HttpClient);

  private readonly apiUrl = API_BASE_URL + API_ENDPOINTS.USERS;

  // Пагинированный метод для management части
  getPaginated(params: UsersQueryParams = {}): Observable<UsersResponse> {
    let httpParams = new HttpParams();

    if (params.limit) {
      httpParams = httpParams.set('limit', params.limit.toString());
    }
    if (params.offset) {
      httpParams = httpParams.set('offset', params.offset.toString());
    }
    if (params.sort) {
      httpParams = httpParams.set('sort', params.sort);
    }

    return this.http
      .get<UsersResponsePaginatedDTO>(this.apiUrl, { params: httpParams })
      .pipe(map((dto) => MapperUtil.usersResponseFromDto(dto)));
  }

  // Оставим старый метод для совместимости, но сделаем его использующим пагинированный API
  getAll(): Observable<UsersResponse> {
    return this.getPaginated({ limit: 1000 }); // Большой лимит для получения всех
  }

  getAllSimple(): Observable<User[]> {
    return this.getAll().pipe(map((response) => response.results));
  }

  getById(id: number): Observable<User> {
    return this.http
      .get<UserDTO>(`${this.apiUrl}${id}/`)
      .pipe(map((dto) => MapperUtil.userFromDto(dto)));
  }

  create(user: Omit<User, 'id'>): Observable<User> {
    const dto = MapperUtil.userToRequestDto({
      ...user,
      isActive: user.isActive,
    });
    return this.http
      .post<UserDTO>(this.apiUrl, dto)
      .pipe(map((dto) => MapperUtil.userFromDto(dto)));
  }

  update(id: number, user: User): Observable<User> {
    const dto = MapperUtil.userToRequestDto(user);
    return this.http
      .put<UserDTO>(`${this.apiUrl}${id}/`, dto)
      .pipe(map((dto) => MapperUtil.userFromDto(dto)));
  }

  partialUpdate(id: number, user: Partial<User>): Observable<User> {
    const dto = MapperUtil.userToRequestDto(user as User);
    return this.http
      .patch<UserDTO>(`${this.apiUrl}${id}/`, dto)
      .pipe(map((dto) => MapperUtil.userFromDto(dto)));
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}${id}/`);
  }
}
