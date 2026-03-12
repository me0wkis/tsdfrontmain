import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, forkJoin } from 'rxjs';
import { map } from 'rxjs/operators';
import {
  API_BASE_URL,
  API_ENDPOINTS,
} from '../../../core/constants/api.constants';
import { Shifts, ShiftsResponse } from '../../../shared/models/shifts.model';
import { ShiftsDTO, ShiftDTO } from '../../../core/DTO/shifts.dto';
import { MapperUtil } from '../../../core/utils/mapper.util';

@Injectable({
  providedIn: 'root',
})
export class ShiftsService {
  private http = inject(HttpClient);

  private readonly apiUrl = API_BASE_URL + API_ENDPOINTS.SHIFTS;

  getAll(): Observable<ShiftsResponse> {
    return this.http
      .get<ShiftsDTO>(this.apiUrl)
      .pipe(map((dto) => MapperUtil.shiftsResponseFromDto(dto)));
  }

  getAllSimple(): Observable<Shifts[]> {
    return this.getAll().pipe(map((response) => response.results));
  }

  getById(id: number): Observable<Shifts> {
    return this.http
      .get<ShiftDTO>(`${this.apiUrl}${id}/`)
      .pipe(map((dto) => MapperUtil.shiftFromDto(dto)));
  }

  create(shift: Omit<Shifts, 'id'>): Observable<Shifts> {
    const dto = MapperUtil.shiftToRequestDto(shift);
    return this.http
      .post<ShiftDTO>(this.apiUrl, dto)
      .pipe(map((dto) => MapperUtil.shiftFromDto(dto)));
  }

  createBulk(shifts: Omit<Shifts, 'id'>[]): Observable<Shifts[]> {
    const dtos = shifts.map((shift) => MapperUtil.shiftToRequestDto(shift));
    return this.http
      .post<ShiftDTO[]>(this.apiUrl, dtos)
      .pipe(map((dtos) => dtos.map((dto) => MapperUtil.shiftFromDto(dto))));
  }

  update(id: number, shift: Shifts): Observable<Shifts> {
    const dto = MapperUtil.shiftToRequestDto(shift);
    return this.http
      .put<ShiftDTO>(`${this.apiUrl}${id}/`, dto)
      .pipe(map((dto) => MapperUtil.shiftFromDto(dto)));
  }

  partialUpdate(id: number, shift: Partial<Shifts>): Observable<Shifts> {
    const dto = MapperUtil.shiftToRequestDto(shift as Shifts);
    return this.http
      .patch<ShiftDTO>(`${this.apiUrl}${id}/`, dto)
      .pipe(map((dto) => MapperUtil.shiftFromDto(dto)));
  }

  updateBulk(
    updates: { id: number; shift: Partial<Shifts> }[]
  ): Observable<Shifts[]> {
    if (updates.length === 0) {
      return new Observable((observer) => {
        observer.next([]);
        observer.complete();
      });
    }

    const updateRequests = updates.map((update) =>
      this.partialUpdate(update.id, update.shift)
    );

    return forkJoin(updateRequests);
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}${id}/`);
  }
}
