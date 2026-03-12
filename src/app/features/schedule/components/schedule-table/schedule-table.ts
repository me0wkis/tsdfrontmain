import {
  Component,
  Input,
  OnInit,
  OnDestroy,
  HostListener,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { ScheduleHeader } from '../schedule-header/schedule-header';
import { ScheduleRow } from '../schedule-row/schedule-row';
import { ScheduleResponse } from '../../../../shared/models/schedule.model';
import { CellSelectionService } from '../../services/cell-selection.service';

@Component({
  selector: 'app-schedule-table',
  standalone: true,
  imports: [CommonModule, ScheduleHeader, ScheduleRow, ProgressSpinnerModule],
  templateUrl: './schedule-table.html',
  styleUrl: './schedule-table.css',
})
export class ScheduleTable {
  @Input() month!: string;
  @Input() days!: {
    day: number;
    isWeekend: boolean;
    dayName: string;
    isHoliday?: boolean;
  }[]; // Дни с флагом выходного, названием дня и праздника
  @Input() scheduleData: ScheduleResponse | null = null; // Данные расписания с API
  @Input() loading = false; // Флаг загрузки
  @Input() isEditMode = false; // Режим редактирования
  @Input() pendingShifts: Map<string, any> = new Map(); // Отложенные смены для создания
  @Input() shiftsToUpdate: Map<string, any> = new Map(); // Отложенные смены для обновления
  @Input() shiftsToDelete: Map<string, any> = new Map(); // Смены на удаление

  constructor(private cellSelectionService: CellSelectionService) {}

  // Глобальный обработчик отпускания кнопки мыши
  @HostListener('document:mouseup', ['$event'])
  onDocumentMouseUp(event: MouseEvent): void {
    if (this.isEditMode) {
      this.cellSelectionService.stopDrawing();
    }
  }

  // Предотвращаем выделение текста во время рисования
  @HostListener('document:selectstart', ['$event'])
  onDocumentSelectStart(event: Event): void {
    if (this.isEditMode && this.cellSelectionService.isCurrentlyDrawing()) {
      event.preventDefault();
    }
  }

  // Предотвращаем контекстное меню во время рисования
  @HostListener('document:contextmenu', ['$event'])
  onDocumentContextMenu(event: MouseEvent): void {
    if (this.isEditMode && this.cellSelectionService.isCurrentlyDrawing()) {
      event.preventDefault();
    }
  }

  // Получить цвет команды для отображения
  getTeamColor(teamName: string): string {
    const teamColors: { [key: string]: string } = {
      'Green Team': '#10B981', // blue
      'Red Team': '#EF4444', // green
      'Yellow Team': '#F59E0B', // orange
    };

    return teamColors[teamName] || '#6B7280'; // default gray
  }
}
