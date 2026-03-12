import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_BASE_URL, API_ENDPOINTS } from '@core/constants/api.constants';
import { TeamDto } from '@core/DTO/teams.dto';
import { Team } from '@shared/models/teams.model';
import { MapperUtil } from '@core/utils/mapper.util';

@Injectable({
  providedIn: 'root',
})
export class TeamsApiService {
  private apiUrl = `${API_BASE_URL}${API_ENDPOINTS.TEAMS}`;

  constructor(private http: HttpClient) {}

  getAll(): Observable<Team[]> {
    return this.http
      .get<TeamDto[]>(this.apiUrl)
      .pipe(map((dtos) => dtos.map((dto) => MapperUtil.teamFromDto(dto))));
  }

  getById(id: number): Observable<Team> {
    return this.http
      .get<TeamDto>(`${this.apiUrl}${id}/`)
      .pipe(map((dto) => MapperUtil.teamFromDto(dto)));
  }

  create(team: Partial<Team>): Observable<Team> {
    return this.http
      .post<TeamDto>(this.apiUrl, team)
      .pipe(map((dto) => MapperUtil.teamFromDto(dto)));
  }

  update(id: number, team: Partial<Team>): Observable<Team> {
    return this.http
      .patch<TeamDto>(`${this.apiUrl}${id}/`, team)
      .pipe(map((dto) => MapperUtil.teamFromDto(dto)));
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}${id}/`);
  }
}
