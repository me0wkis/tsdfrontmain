import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { API_BASE_URL, API_ENDPOINTS } from '@core/constants/api.constants';
import { ShiftTemplates } from '@shared/models/shifts.model';
import { ShiftTemplatesDTO } from '@core/DTO/shifts.dto';
import { MapperUtil } from '@core/utils/mapper.util';

@Injectable({
  providedIn: 'root',
})
export class ShiftTemplatesService {
  private http = inject(HttpClient);

  private readonly apiUrl = API_BASE_URL + API_ENDPOINTS.SHIFT_TEMPLATES;

  getAll(): Observable<ShiftTemplates[]> {
    return this.http
      .get<ShiftTemplatesDTO[]>(this.apiUrl)
      .pipe(
        map((dtos) => dtos.map((dto) => MapperUtil.shiftTemplateFromDto(dto)))
      );
  }

  getByShiftType(shiftTypeId: number): Observable<ShiftTemplates[]> {
    return this.http
      .get<ShiftTemplatesDTO[]>(`${this.apiUrl}?shift_type=${shiftTypeId}`)
      .pipe(
        map((dtos) => dtos.map((dto) => MapperUtil.shiftTemplateFromDto(dto)))
      );
  }

  getById(id: number): Observable<ShiftTemplates> {
    return this.http
      .get<ShiftTemplatesDTO>(`${this.apiUrl}${id}/`)
      .pipe(map((dto) => MapperUtil.shiftTemplateFromDto(dto)));
  }

  create(
    shiftTemplate: Omit<ShiftTemplates, 'id'>
  ): Observable<ShiftTemplates> {
    const dto = MapperUtil.shiftTemplateToRequestDto(shiftTemplate);
    return this.http
      .post<ShiftTemplatesDTO>(this.apiUrl, dto)
      .pipe(map((dto) => MapperUtil.shiftTemplateFromDto(dto)));
  }

  update(
    id: number,
    shiftTemplate: ShiftTemplates
  ): Observable<ShiftTemplates> {
    const dto = MapperUtil.shiftTemplateToRequestDto(shiftTemplate);
    return this.http
      .put<ShiftTemplatesDTO>(`${this.apiUrl}${id}/`, dto)
      .pipe(map((dto) => MapperUtil.shiftTemplateFromDto(dto)));
  }

  partialUpdate(
    id: number,
    shiftTemplate: Partial<ShiftTemplates>
  ): Observable<ShiftTemplates> {
    const dto = MapperUtil.shiftTemplateToRequestDto(
      shiftTemplate as ShiftTemplates
    );
    return this.http
      .patch<ShiftTemplatesDTO>(`${this.apiUrl}${id}/`, dto)
      .pipe(map((dto) => MapperUtil.shiftTemplateFromDto(dto)));
  }

  delete(id: number): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}${id}/`);
  }
}
