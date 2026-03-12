import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-schedule-header',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './schedule-header.html',
})
export class ScheduleHeader {
  @Input() month!: string; // Месяц
  @Input() days!: {
    day: number;
    isWeekend: boolean;
    dayName: string;
    isHoliday?: boolean;
  }[]; // Дни с флагом выходного, названием дня и праздника
}
