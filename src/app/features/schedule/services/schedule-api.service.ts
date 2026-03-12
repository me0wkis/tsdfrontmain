import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import {
  API_BASE_URL,
  API_ENDPOINTS,
} from '../../../core/constants/api.constants';
import { MapperUtil } from '../../../core/utils/mapper.util';
import { ScheduleResponseDTO } from '../../../core/DTO/schedule.dto';
import {
  CalendarAnomalyDTO,
  AnomaliesResponseDTO,
} from '../../../core/DTO/anomalies.dto';
import { ScheduleResponse } from '../../../shared/models/schedule.model';
import { AnomaliesResponse } from '../../../shared/models/anomalies.model';

@Injectable({
  providedIn: 'root',
})
export class ScheduleApiService {
  private http = inject(HttpClient); // Делаем public для отладки

  /**
   * Получить расписание на указанный месяц
   * @param year - год (например, 2025)
   * @param month - месяц (например, 09)
   * @param includeAllActive - включить всех активных пользователей (для edit mode)
   * @returns Observable<ScheduleResponse>
   */
  getSchedule(
    year: number,
    month: string,
    includeAllActive: boolean = false
  ): Observable<ScheduleResponse> {
    const params = includeAllActive ? '?include_all_active=1' : '';
    const url = `${API_BASE_URL}${API_ENDPOINTS.SCHEDULE}${year}/${month}/${params}`;
    return this.http.get<ScheduleResponseDTO>(url).pipe(
      map((dto) => {
        console.log('Raw schedule DTO from server:', dto);
        try {
          const mapped = MapperUtil.scheduleFromDto(dto);
          return mapped;
        } catch (error) {
          console.error('Error mapping schedule data:', error);
          // Возвращаем пустой объект в случае ошибки маппинга
          return {
            year: year,
            month: parseInt(month),
            monthName: '',
            teams: [],
          };
        }
      })
    );
  }

  /**
   * Получить аномалии календаря на указанный месяц
   * @param year - год (например, 2025)
   * @param month - месяц (например, 09)
   * @returns Observable<CalendarAnomaliesResponse>
   */
  getCalendarAnomalies(
    year: number,
    month: string
  ): Observable<AnomaliesResponse> {
    const url = `${API_BASE_URL}${API_ENDPOINTS.CALENDAR_ANOMALIES}${year}/${month}/`;
    return this.http.get<AnomaliesResponseDTO>(url).pipe(
      map((dto) => {
        try {
          return MapperUtil.anomaliesResponseFromDto(dto);
        } catch (error) {
          console.error('Error mapping anomalies data:', error);
          // Возвращаем пустой объект в случае ошибки маппинга
          return {
            year: year,
            month: parseInt(month),
            anomalies: [],
          };
        }
      })
    );
  }
}
