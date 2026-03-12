import { Component, Input, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TooltipModule } from 'primeng/tooltip';
import { Shift } from '../../../../shared/models/schedule.model';
import {
  CellSelectionService,
  SelectedCell,
} from '../../services/cell-selection.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-schedule-cell',
  standalone: true,
  imports: [CommonModule, TooltipModule],
  templateUrl: './schedule-cell.html',
  styleUrl: './schedule-cell.css',
})
export class ScheduleCell implements OnInit, OnDestroy {
  @Input() shiftData!: {
    day: number;
    shiftType: string;
    color: string;
    shift?: Shift;
  };
  @Input() isWeekend: boolean = false;
  @Input() isHoliday: boolean = false;
  @Input() isEditMode: boolean = false;
  @Input() userId!: string;
  @Input() year!: number;
  @Input() month!: number;
  @Input() day!: number;
  @Input() pendingShifts: Map<string, any> = new Map();
  @Input() shiftsToUpdate: Map<string, any> = new Map();
  @Input() shiftsToDelete: Map<string, any> = new Map();

  isSelected: boolean = false;
  isUserSelected: boolean = false;

  private selectionSubscription!: Subscription;
  private userSelectionSubscription!: Subscription;

  private cellSelectionService = inject(CellSelectionService);

  ngOnInit(): void {
    // Подписываемся на изменения выбранных ячеек
    this.selectionSubscription =
      this.cellSelectionService.selectedCells$.subscribe((selectedCells) => {
        this.isSelected = selectedCells.some(
          (cell) => cell.cellId === this.cellId
        );
      });

    // Подписываемся на изменения выбранных пользователей
    this.userSelectionSubscription =
      this.cellSelectionService.selectedUsers$.subscribe((selectedUsers) => {
        this.isUserSelected = selectedUsers.includes(this.userId);
      });
  }

  ngOnDestroy(): void {
    if (this.selectionSubscription) {
      this.selectionSubscription.unsubscribe();
    }
    if (this.userSelectionSubscription) {
      this.userSelectionSubscription.unsubscribe();
    }
  }

  // Генерируем ID ячейки
  get cellId(): string {
    const day = this.shiftData.day.toString().padStart(2, '0');
    const month = this.month.toString().padStart(2, '0');
    return `${this.userId}-${this.year}${month}${day}`;
  }

  // Генерируем дату в формате YYYY-MM-DD
  get cellDate(): string {
    const day = this.shiftData.day.toString().padStart(2, '0');
    const month = this.month.toString().padStart(2, '0');
    return `${this.year}-${month}-${day}`;
  }

  // Создать объект SelectedCell для текущей ячейки
  private createSelectedCell(): SelectedCell {
    return {
      userId: this.userId,
      date: this.cellDate,
      cellId: this.cellId,
      shiftId: this.shiftData.shift?.id,
    };
  }

  // Обработчик начала выделения (mousedown)
  onMouseDown(event: MouseEvent): void {
    if (this.isEditMode) {
      event.preventDefault();
      this.cellSelectionService.startDrawing(
        this.createSelectedCell(),
        event.ctrlKey
      );
    }
  }

  // Обработчик наведения во время рисования (mouseenter)
  onMouseEnter(): void {
    if (this.isEditMode && this.cellSelectionService.isCurrentlyDrawing()) {
      this.cellSelectionService.continueDrawing(this.createSelectedCell());
    }
  }

  // Обработчик окончания выделения (mouseup)
  onMouseUp(): void {
    if (this.isEditMode) {
      this.cellSelectionService.stopDrawing();
    }
  }

  // Обработчик простого клика (для переключения отдельных ячеек)
  onCellClick(event: MouseEvent): void {
    if (
      this.isEditMode &&
      !this.cellSelectionService.isCurrentlyDrawing() &&
      !this.cellSelectionService.wasRecentlyDrawing()
    ) {
      event.preventDefault();
      this.cellSelectionService.handleCellClick(this.createSelectedCell());
    }
  }

  // Проверяем, является ли смена студенческой
  get isStudentShift(): boolean {
    return this.shiftData.shift?.jobTitle === 'Student';
  }

  // Получить время работы для студентов (например, "14-18")
  get studentWorkTime(): string {
    if (!this.isStudentShift || !this.shiftData.shift) {
      return '';
    }

    const startHour = this.getHourFromTime(this.shiftData.shift.startTime);
    const endHour = this.getHourFromTime(this.shiftData.shift.endTime);

    if (startHour && endHour) {
      return `${startHour}-${endHour}`;
    }

    return '';
  }

  // Извлекаем только час из времени
  private getHourFromTime(time: string): string {
    if (!time) return '';
    const parts = time.split(':');
    return parts.length > 0 ? parts[0] : '';
  }

  // Форматируем время для более читаемого вида
  formatTime(time: string): string {
    if (!time) return '';

    // Время приходит в формате "HH:MM:SS", оставляем только "HH:MM"
    const parts = time.split(':');
    if (parts.length >= 2) {
      return `${parts[0]}:${parts[1]}`;
    }
    return time;
  }

  // Проверить, есть ли pending shift для этой ячейки (новая смена)
  get hasPendingShift(): boolean {
    return this.pendingShifts.has(this.cellId);
  }

  // Получить код pending shift (новая смена)
  get pendingShiftCode(): string {
    const pending = this.pendingShifts.get(this.cellId);
    if (pending) {
      return pending.shiftTemplateCode + pending.shiftTypeCode;
    }
    return '';
  }

  // Проверить, есть ли pending update для этой ячейки (обновление существующей смены)
  get hasPendingUpdate(): boolean {
    return this.shiftsToUpdate.has(this.cellId);
  }

  // Получить код pending update (обновление смены)
  get pendingUpdateCode(): string {
    const pending = this.shiftsToUpdate.get(this.cellId);
    if (pending) {
      return pending.shiftTemplateCode + pending.shiftTypeCode;
    }
    return '';
  }

  // Проверить, отмечена ли смена на удаление
  get isMarkedForDeletion(): boolean {
    return this.shiftsToDelete.has(this.cellId);
  }
}
