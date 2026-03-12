import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ScheduleCell } from '../schedule-cell/schedule-cell';
import { Shift } from '../../../../shared/models/schedule.model';
import { CellSelectionService } from '../../services/cell-selection.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-schedule-row',
  standalone: true,
  imports: [CommonModule, ScheduleCell],
  templateUrl: './schedule-row.html',
  styleUrl: './schedule-row.css',
})
export class ScheduleRow implements OnInit, OnDestroy {
  // Все данные приходят из родительского компонента
  // Принимаем данные пользователя и его смены
  @Input() user!: { id: string; name: string };
  // Принимаем массив смен пользователя из API
  @Input() shifts!: Shift[];
  // Принимаем массив дней с флагом выходного, названием дня и праздника
  @Input() days!: {
    day: number;
    isWeekend: boolean;
    dayName: string;
    isHoliday?: boolean;
  }[];
  // Цвет команды для фона плашки с именем
  @Input() teamColor!: string;
  // Год и месяц для форматирования дат
  @Input() year!: number;
  @Input() month!: number;
  // Режим редактирования
  @Input() isEditMode = false;
  // Отложенные смены для создания
  @Input() pendingShifts: Map<string, any> = new Map();
  // Отложенные смены для обновления
  @Input() shiftsToUpdate: Map<string, any> = new Map();
  // Смены на удаление
  @Input() shiftsToDelete: Map<string, any> = new Map();

  // Состояние выделения пользователя
  isUserSelected = false;
  private userSelectionSubscription!: Subscription;

  constructor(private cellSelectionService: CellSelectionService) {}

  ngOnInit(): void {
    // Подписываемся на изменения выбранных пользователей
    this.userSelectionSubscription =
      this.cellSelectionService.selectedUsers$.subscribe((selectedUsers) => {
        this.isUserSelected = selectedUsers.includes(this.user.id);
      });
  }

  ngOnDestroy(): void {
    if (this.userSelectionSubscription) {
      this.userSelectionSubscription.unsubscribe();
    }
  }

  // Обработчик клика по имени пользователя
  onUserNameClick(event: MouseEvent): void {
    if (this.isEditMode) {
      event.preventDefault();
      this.cellSelectionService.toggleUserSelection(this.user.id);
    }
  }

  getShiftForDay(day: number): {
    day: number;
    shiftType: string;
    color: string;
    shift?: Shift;
  } {
    // Ищем смену на указанную дату
    const targetDate = this.formatDateForDay(day);
    const shift = this.shifts.find((s) => s.shiftDate === targetDate);

    if (shift) {
      return {
        day: day,
        shiftType: shift.shortCode,
        color: this.getShiftColor(shift.shortCode),
        shift: shift,
      };
    }

    return {
      day: day,
      shiftType: '',
      color: '',
    };
  }

  // Форматирует день в строку даты YYYY-MM-DD
  private formatDateForDay(day: number): string {
    return `${this.year}-${this.month.toString().padStart(2, '0')}-${day
      .toString()
      .padStart(2, '0')}`;
  }

  // Получить цвет для типа смены
  private getShiftColor(shortCode: string): string {
    const shiftColors: { [key: string]: string } = {
      '3C': '#1890FF', // blue - central shift
      '3L': '#F59E0B', // orange - late shift
      '3E': '#10B981', // green - early shift
      '3P': '#8B5CF6', // purple - premium shift
      '7C': '#1890FF', // blue
      '6C': '#1890FF', // light blue
      '2E': '#10B981', // green
      '6E': '#059669', // dark green
      '2L': '#F97316', // orange
      '7L': '#F97316', // dark orange
      P: '#8B5CF6', // purple
    };

    return shiftColors[shortCode] || '#6B7280'; // default gray
  }
}
