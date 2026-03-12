import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_BASE_URL, API_ENDPOINTS } from '@core/constants/api.constants';
import { ShiftTypes } from '@shared/models/shifts.model';
import { ShiftTypesDTO } from '@core/DTO/shifts.dto';
import { MapperUtil } from '@/core/utils/mapper.util';

@Injectable({
  providedIn: 'root',
})
export class ShiftTypesService {
  private http = inject(HttpClient);

  private readonly apiUrl = API_BASE_URL + API_ENDPOINTS.SHIFT_TYPES;

  getAll(): Observable<ShiftTypes[]> {
    return this.http
      .get<ShiftTypesDTO[]>(this.apiUrl)
      .pipe(map((dtos) => dtos.map((dto) => MapperUtil.shiftTypeFromDto(dto))));
  }

  getById(id: number): Observable<ShiftTypes> {
    return this.http
      .get<ShiftTypesDTO>(`${this.apiUrl}${id}/`)
      .pipe(map((dto) => MapperUtil.shiftTypeFromDto(dto)));
  }

  create(shiftType: Omit<ShiftTypes, 'id'>): Observable<ShiftTypes> {
    const dto = MapperUtil.shiftTypeToRequestDto(shiftType);
    return this.http
      .post<ShiftTypesDTO>(this.apiUrl, dto)
      .pipe(map((dto) => MapperUtil.shiftTypeFromDto(dto)));
  }

  update(id: number, shiftType: ShiftTypes): Observable<ShiftTypes> {
    const dto = MapperUtil.shiftTypeToRequestDto(shiftType);
    return this.http
      .put<ShiftTypesDTO>(`${this.apiUrl}${id}/`, dto)
      .pipe(map((dto) => MapperUtil.shiftTypeFromDto(dto)));
  }

  partialUpdate(
    id: number,
    shiftType: Partial<ShiftTypes>
  ): Observable<ShiftTypes> {
    const dto = MapperUtil.shiftTypeToRequestDto(shiftType as ShiftTypes);
    return this.http
      .patch<ShiftTypesDTO>(`${this.apiUrl}${id}/`, dto)
      .pipe(map((dto) => MapperUtil.shiftTypeFromDto(dto)));
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}${id}/`);
  }
}
