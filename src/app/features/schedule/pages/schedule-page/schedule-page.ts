import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { forkJoin, Subscription } from 'rxjs';
import { FormsModule } from '@angular/forms';
import {
  trigger,
  state,
  style,
  transition,
  animate,
} from '@angular/animations';

import { ButtonModule } from 'primeng/button';
import { SkeletonModule } from 'primeng/skeleton';
import { SelectModule } from 'primeng/select';
import { ScrollPanelModule } from 'primeng/scrollpanel';
import { InputTextModule } from 'primeng/inputtext';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ConfirmationService } from 'primeng/api';
import { ScheduleTable } from '../../components/schedule-table/schedule-table';
import { MainLayout } from '@core/layouts/main-layout/main-layout';
import { ScheduleApiService } from '../../services/schedule-api.service';
import { ShiftTypesService } from 'features/management/services/shift-types-api.service';
import { ShiftTemplatesService } from 'features/management/services/shift-templates-api.service';
import { ShiftsService } from 'features/management/services/shifts-api.service';
import {
  CellSelectionService,
  SelectedCell,
} from '../../services/cell-selection.service';
// Schedule models
import { ScheduleResponse } from '@shared/models/schedule.model';
import {
  AnomaliesResponse,
  CalendarAnomaly,
} from '@shared/models/anomalies.model';
import { ShiftTypes, ShiftTemplates } from '@shared/models/shifts.model';

// Интерфейс для отложенных смен (новые смены)
interface PendingShift {
  cellId: string;
  userId: string;
  date: string;
  shiftTypeId: number;
  shiftTemplateId: number;
  shiftTypeCode: string;
  shiftTemplateCode: string;
}

// Интерфейс для смен на обновление (существующие смены)
interface PendingShiftUpdate {
  cellId: string;
  shiftId: number;
  userId: string;
  date: string;
  shiftTypeId: number;
  shiftTemplateId: number;
  shiftTypeCode: string;
  shiftTemplateCode: string;
}

// Интерфейс для смен на удаление
interface ShiftToDelete {
  cellId: string;
  userId: string;
  date: string;
  shiftId?: number;
}

@Component({
  selector: 'app-schedule-page',
  standalone: true,
  imports: [
    ScheduleTable,
    ButtonModule,
    SkeletonModule,
    SelectModule,
    ScrollPanelModule,
    InputTextModule,
    ConfirmDialogModule,
    MainLayout,
    CommonModule,
    FormsModule,
  ],
  providers: [ConfirmationService],
  templateUrl: './schedule-page.html',
  animations: [
    trigger('slideDown', [
      transition(':enter', [
        style({ height: '0', opacity: 0, overflow: 'hidden' }),
        animate('200ms ease-out', style({ height: '*', opacity: 1 })),
      ]),
      transition(':leave', [
        style({ height: '*', opacity: 1, overflow: 'hidden' }),
        animate('200ms ease-in', style({ height: '0', opacity: 0 })),
      ]),
    ]),
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('200ms ease-out', style({ opacity: 1 })),
      ]),
      transition(':leave', [
        style({ opacity: 1 }),
        animate('200ms ease-in', style({ opacity: 0 })),
      ]),
    ]),
  ],
})
export class SchedulePage implements OnInit, OnDestroy {
  // Инъекции зависимостей
  route = inject(ActivatedRoute);
  router = inject(Router);
  scheduleApiService = inject(ScheduleApiService);
  cellSelectionService = inject(CellSelectionService);
  shiftTypesService = inject(ShiftTypesService);
  shiftTemplatesService = inject(ShiftTemplatesService);
  shiftsService = inject(ShiftsService);
  confirmationService = inject(ConfirmationService);

  // Подписки на выделения
  private selectionSubscription!: Subscription;
  private userSelectionSubscription!: Subscription;
  selectedCells: SelectedCell[] = [];
  selectedUsers: string[] = [];

  // Параметры для отображения календаря
  // year - год, month - месяц (1-12)
  // monthName - название месяца, days - массив дней с информацией о выходных
  year!: number;
  month!: number;
  monthName: string = '';
  days: {
    day: number;
    isWeekend: boolean;
    dayName: string;
    isHoliday?: boolean;
  }[] = [];

  // Данные с API
  scheduleData: ScheduleResponse | null = null;
  anomaliesData: AnomaliesResponse | null = null;
  loading = false;

  // Режим редактирования
  isEditMode = false;

  // Типы смен для select
  shiftTypes: ShiftTypes[] = [];
  selectedShiftType: ShiftTypes | null = null;

  // Шаблоны смен для выбранного типа
  shiftTemplates: ShiftTemplates[] = [];
  loadingTemplates = false;

  // Выбранный шаблон смены
  selectedTemplate: ShiftTemplates | null = null;

  // Временные поля для гибких смен
  flexibleStartTime: string = '';
  flexibleEndTime: string = '';
  flexibleLunchStartTime: string = '';
  flexibleLunchEndTime: string = '';

  // Отложенные смены для создания (до нажатия Apply)
  pendingShifts: Map<string, PendingShift> = new Map();

  // Отложенные смены для обновления (до нажатия Apply)
  shiftsToUpdate: Map<string, PendingShiftUpdate> = new Map();

  savingShifts = false;

  // Смены на удаление (до нажатия Apply)
  shiftsToDelete: Map<string, ShiftToDelete> = new Map();

  // Массив месяцев для sidebar
  months = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ];

  ngOnInit() {
    this.createMonthDays();
    this.updateCalendar();
    this.loadShiftTypes();

    // Подписываемся на изменения выбранных ячеек
    this.selectionSubscription =
      this.cellSelectionService.selectedCells$.subscribe((selectedCells) => {
        this.selectedCells = selectedCells;
        console.log('Выбранные ячейки обновлены:', selectedCells);
      });

    // Подписываемся на изменения выбранных пользователей
    this.userSelectionSubscription =
      this.cellSelectionService.selectedUsers$.subscribe((selectedUsers) => {
        this.selectedUsers = selectedUsers;
        console.log('Выбранные пользователи обновлены:', selectedUsers);
      });
  }

  ngOnDestroy() {
    if (this.selectionSubscription) {
      this.selectionSubscription.unsubscribe();
    }
    if (this.userSelectionSubscription) {
      this.userSelectionSubscription.unsubscribe();
    }
  }

  createMonthDays() {
    this.route.paramMap.subscribe((params) => {
      const yearParam = params.get('year');
      const monthParam = params.get('month');
      if (yearParam && monthParam) {
        this.year = +yearParam;
        this.month = +monthParam;
        this.updateCalendar();
      } else {
        // Редирект на текущий месяц, если параметры не заданы
        const today = new Date();
        this.router.navigate(
          ['/schedule', today.getFullYear(), today.getMonth() + 1],
          { replaceUrl: true }
        );
      }
    });
  }

  updateCalendar() {
    this.monthName = this.getMonthName(this.month);
    this.loadScheduleData();
  }

  // Переход на предыдущий месяц
  prevMonth() {
    let year = this.year;
    let month = this.month - 1;
    if (month < 1) {
      month = 12;
      year--;
    }
    this.router.navigate(['/schedule', year, month]);
  }

  // Переход на следующий месяц
  nextMonth() {
    let year = this.year;
    let month = this.month + 1;
    if (month > 12) {
      month = 1;
      year++;
    }
    this.router.navigate(['/schedule', year, month]);
  }

  // Выбор конкретного месяца
  selectMonth(selectedMonth: number) {
    this.router.navigate(['/schedule', this.year, selectedMonth]);
  }

  // Генерация дней для указанного месяца
  // Возвращает массив объектов days
  generateDays(year: number, month: number) {
    const daysInMonth = new Date(year, month, 0).getDate();
    const days = [];
    const dayNames = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'];

    for (let i = 1; i <= daysInMonth; i++) {
      const date = new Date(year, month - 1, i);
      const dayOfWeek = date.getDay(); // 0 - воскресенье, 6 - суббота
      const dateString = `${year}-${month.toString().padStart(2, '0')}-${i
        .toString()
        .padStart(2, '0')}`;

      // Проверяем, есть ли аномалия на эту дату
      const isHoliday =
        this.anomaliesData?.anomalies.some(
          (anomaly: CalendarAnomaly) => anomaly.date === dateString
        ) || false;

      days.push({
        day: i,
        isWeekend: dayOfWeek === 0 || dayOfWeek === 6,
        dayName: dayNames[dayOfWeek],
        isHoliday: isHoliday,
      });
    }
    return days;
  }

  getMonthName(month: number): string {
    const months = [
      'JANUARY',
      'FEBRUARY',
      'MARCH',
      'APRIL',
      'MAY',
      'JUNE',
      'JULY',
      'AUGUST',
      'SEPTEMBER',
      'OCTOBER',
      'NOVEMBER',
      'DECEMBER',
    ];
    return months[month - 1];
  }

  // Переход к текущему месяцу
  goToCurrentMonth() {
    const today = new Date();
    this.router.navigate([
      '/schedule',
      today.getFullYear(),
      today.getMonth() + 1,
    ]);
  }

  editSchedule() {
    // Переключение режима редактирования
    this.isEditMode = !this.isEditMode;
    console.log('Edit mode:', this.isEditMode ? 'ON' : 'OFF');

    // Очистить все выделения при выходе из режима редактирования
    if (!this.isEditMode) {
      this.cellSelectionService.clearAllSelections();
    }

    // Перезагружаем данные с учетом нового режима
    // В режиме редактирования загрузим всех активных пользователей
    this.loadScheduleData();
  }

  // Загрузка типов смен
  loadShiftTypes() {
    this.shiftTypesService.getAll().subscribe({
      next: (data) => {
        this.shiftTypes = data;
        console.log('Типы смен загружены:', data);
      },
      error: (error) => {
        console.error('Ошибка загрузки типов смен:', error);
      },
    });
  }

  // Обработчик изменения типа смены
  onShiftTypeChange(shiftType: ShiftTypes) {
    this.selectedShiftType = shiftType;
    console.log('Выбран тип смены:', shiftType);

    // Очищаем выбранный шаблон и поля времени
    this.selectedTemplate = null;
    this.flexibleStartTime = '';
    this.flexibleEndTime = '';
    this.flexibleLunchStartTime = '';
    this.flexibleLunchEndTime = '';

    if (shiftType && shiftType.id) {
      this.loadShiftTemplates(shiftType.id);
    } else {
      this.shiftTemplates = [];
    }
  }

  // Очистка выбранного шаблона и полей времени
  clearTemplateSelection() {
    this.selectedTemplate = null;
    this.flexibleStartTime = '';
    this.flexibleEndTime = '';
    this.flexibleLunchStartTime = '';
    this.flexibleLunchEndTime = '';
    console.log('Очищен выбор шаблона');
  }

  // Загрузка шаблонов смен по типу смены
  loadShiftTemplates(shiftTypeId: number) {
    this.loadingTemplates = true;
    this.shiftTemplatesService.getByShiftType(shiftTypeId).subscribe({
      next: (data) => {
        this.shiftTemplates = data;
        this.loadingTemplates = false;
        console.log('Шаблоны смен загружены:', data);
      },
      error: (error) => {
        console.error('Ошибка загрузки шаблонов смен:', error);
        this.shiftTemplates = [];
        this.loadingTemplates = false;
      },
    });
  }

  // Выбор шаблона смены
  selectTemplate(template: ShiftTemplates) {
    this.selectedTemplate = template;
    console.log('Выбран шаблон смены:', template);

    // Если шаблон с фиксированным временем, заполняем поля автоматически
    if (template.isFixedTime) {
      this.flexibleStartTime = template.startTime;
      this.flexibleEndTime = template.endTime;
      this.flexibleLunchStartTime = template.lunchStartTime;
      this.flexibleLunchEndTime = template.lunchEndTime;
    } else {
      // Очищаем поля для гибких смен
      this.flexibleStartTime = '';
      this.flexibleEndTime = '';
      this.flexibleLunchStartTime = '';
      this.flexibleLunchEndTime = '';
    }
  }

  // Очистить все выделения
  clearAllSelections() {
    this.cellSelectionService.clearAllSelections();
  }

  // Получить имя пользователя по ID
  getUserName(userId: string): string {
    if (!this.scheduleData) return userId;

    for (const team of this.scheduleData.teams) {
      const user = team.users.find((u) => u.id.toString() === userId);
      if (user) {
        return user.fullName;
      }
    }
    return userId;
  }

  // Загрузка данных расписания и аномалий
  loadScheduleData() {
    this.loading = true;
    const monthStr = this.month.toString().padStart(2, '0');

    console.log(
      'Загружаем данные для:',
      this.year,
      monthStr,
      'Edit mode:',
      this.isEditMode
    );

    forkJoin({
      schedule: this.scheduleApiService.getSchedule(
        this.year,
        monthStr,
        this.isEditMode // Если edit mode - загружаем всех активных пользователей
      ),
      anomalies: this.scheduleApiService.getCalendarAnomalies(
        this.year,
        monthStr
      ),
    }).subscribe({
      next: (data) => {
        console.log('Данные загружены:', data);
        console.log('Schedule teams:', data.schedule?.teams);
        console.log('Anomalies:', data.anomalies?.anomalies);

        this.scheduleData = data.schedule;
        this.anomaliesData = data.anomalies;

        // Проверяем, есть ли команды в данных
        if (
          data.schedule &&
          data.schedule.teams &&
          data.schedule.teams.length > 0
        ) {
          console.log('Найдено команд:', data.schedule.teams.length);
        } else {
          console.log('Нет команд в данных расписания');
        }

        // Перегенерируем дни с учетом полученных аномалий
        this.days = this.generateDays(this.year, this.month);
        this.loading = false;
      },
      error: (error) => {
        console.error('Ошибка загрузки данных:', error);
        // В случае ошибки генерируем дни без аномалий
        this.days = this.generateDays(this.year, this.month);
        this.loading = false;
      },
    });
  }

  // Получить цвет команды для отображения
  getTeamColor(teamName: string): string {
    const teamColors: { [key: string]: string } = {
      'Team Alpha': '#3B82F6', // blue
      'Team Beta': '#10B981', // green
      'Team Gamma': '#F59E0B', // orange
      'Team Delta': '#EF4444', // red
      'Team Echo': '#8B5CF6', // purple
      'Team Foxtrot': '#06B6D4', // cyan
    };

    return teamColors[teamName] || '#6B7280'; // default gray
  }

  // Получить цвет для шаблона смены на основе кода
  getShiftTemplateColor(code: string): string {
    // Генерируем цвет на основе кода смены
    const colors = [
      '#3B82F6', // blue
      '#10B981', // green
      '#F59E0B', // orange
      '#EF4444', // red
      '#8B5CF6', // purple
      '#06B6D4', // cyan
      '#EC4899', // pink
      '#14B8A6', // teal
    ];

    // Простое хеширование кода для получения индекса цвета
    let hash = 0;
    for (let i = 0; i < code.length; i++) {
      hash = code.charCodeAt(i) + ((hash << 5) - hash);
    }
    const index = Math.abs(hash) % colors.length;
    return colors[index];
  }

  // Получить комбинированный код смены (template + type)
  getCombinedShiftCode(template: ShiftTemplates): string {
    const templateCode = template.code || '';
    const typeCode = this.selectedShiftType?.code || '';

    // Если есть оба кода - объединяем
    if (templateCode && typeCode) {
      return templateCode + typeCode;
    }

    // Если есть только один - показываем его
    return templateCode || typeCode || '?';
  }

  // Назначить смену на выбранные ячейки
  assignShiftsToCells() {
    if (!this.selectedShiftType || !this.selectedTemplate) {
      console.warn('Не выбран тип смены или шаблон');
      return;
    }

    // Проходим по всем выбранным ячейкам
    this.selectedCells.forEach((cell) => {
      // Парсим cellId: формат userId-date (например: 63403-20250902)
      const parts = cell.cellId.split('-');
      if (parts.length < 2) {
        console.error('Неверный формат cellId:', cell.cellId);
        return;
      }

      const userId = parts[0];
      const dateStr = parts[1]; // формат YYYYMMDD

      // Преобразуем дату в формат YYYY-MM-DD
      const year = dateStr.substring(0, 4);
      const month = dateStr.substring(4, 6);
      const day = dateStr.substring(6, 8);
      const formattedDate = `${year}-${month}-${day}`;

      // Проверяем, есть ли у ячейки существующая смена
      if (cell.shiftId) {
        // Смена существует - готовим к обновлению
        const pendingUpdate: PendingShiftUpdate = {
          cellId: cell.cellId,
          shiftId: cell.shiftId,
          userId: userId,
          date: formattedDate,
          shiftTypeId: this.selectedShiftType!.id,
          shiftTemplateId: this.selectedTemplate!.id,
          shiftTypeCode: this.selectedShiftType!.code,
          shiftTemplateCode: this.selectedTemplate!.code,
        };

        this.shiftsToUpdate.set(cell.cellId, pendingUpdate);

        // Убираем из других списков, если там была
        this.pendingShifts.delete(cell.cellId);
        this.shiftsToDelete.delete(cell.cellId);
      } else {
        // Смены нет - готовим к созданию
        const pendingShift: PendingShift = {
          cellId: cell.cellId,
          userId: userId,
          date: formattedDate,
          shiftTypeId: this.selectedShiftType!.id,
          shiftTemplateId: this.selectedTemplate!.id,
          shiftTypeCode: this.selectedShiftType!.code,
          shiftTemplateCode: this.selectedTemplate!.code,
        };

        this.pendingShifts.set(cell.cellId, pendingShift);

        // Убираем из других списков, если там была
        this.shiftsToUpdate.delete(cell.cellId);
        this.shiftsToDelete.delete(cell.cellId);
      }
    });

    console.log('Назначено смен для создания:', this.pendingShifts.size);
    console.log('Назначено смен для обновления:', this.shiftsToUpdate.size);
  }

  // Очистить все назначения
  clearPendingShifts() {
    this.pendingShifts.clear();
    this.shiftsToUpdate.clear();
    this.shiftsToDelete.clear();
    console.log('Все назначения очищены');
  }

  // Отметить все смены выбранного пользователя на удаление
  clearUserShifts() {
    if (this.selectedUsers.length === 0) {
      console.warn('Пользователь не выбран');
      return;
    }

    // Проходим по всем выбранным пользователям
    this.selectedUsers.forEach((userId) => {
      // Проходим по всем дням месяца
      this.days.forEach((day) => {
        const dayStr = day.day.toString().padStart(2, '0');
        const monthStr = this.month.toString().padStart(2, '0');
        const cellId = `${userId}-${this.year}${monthStr}${dayStr}`;

        // Находим смену для этой ячейки в scheduleData
        let shiftId: number | undefined;
        if (this.scheduleData) {
          for (const team of this.scheduleData.teams) {
            const user = team.users.find((u) => u.id.toString() === userId);
            if (user) {
              const dateStr = `${this.year}-${monthStr}-${dayStr}`;
              const shift = user.shifts.find((s) => s.shiftDate === dateStr);
              if (shift) {
                shiftId = shift.id;
              }
            }
          }
        }

        // Добавляем в список на удаление
        const shiftToDelete: ShiftToDelete = {
          cellId: cellId,
          userId: userId,
          date: `${this.year}-${monthStr}-${dayStr}`,
          shiftId: shiftId,
        };

        this.shiftsToDelete.set(cellId, shiftToDelete);
      });
    });

    console.log('Отмечено смен на удаление:', this.shiftsToDelete.size);
  }

  // Очистить только выбранные смены (с подтверждением)
  clearSelectedShifts() {
    if (this.selectedCells.length === 0) {
      console.warn('Ячейки не выбраны');
      return;
    }

    // Фильтруем только те ячейки, в которых есть смены
    const cellsWithShifts = this.selectedCells.filter((cell) => cell.shiftId);

    if (cellsWithShifts.length === 0) {
      console.warn('Среди выбранных ячеек нет смен для удаления');
      return;
    }

    // Показываем диалог подтверждения
    this.showDeleteConfirmation(cellsWithShifts);
  }

  // Показать диалог подтверждения удаления выбранных смен
  showDeleteConfirmation(cellsWithShifts: SelectedCell[]) {
    const shiftsInfo = cellsWithShifts
      .map((cell) => {
        const userName = this.getUserName(cell.userId);
        const formattedDate = new Date(cell.date).toLocaleDateString('ru-RU', {
          day: '2-digit',
          month: '2-digit',
          year: 'numeric',
        });
        return `• ${userName} - ${formattedDate}`;
      })
      .join('\n');

    const message = `Вы собираетесь удалить ${cellsWithShifts.length} смен:\n\n${shiftsInfo}\n\nПродолжить?`;

    this.confirmationService.confirm({
      header: 'Подтверждение удаления смен',
      message: message,
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Да, удалить',
      rejectLabel: 'Отмена',
      acceptButtonStyleClass: 'p-button-danger',
      rejectButtonStyleClass: 'p-button-text',
      accept: () => {
        this.executeDeleteSelectedShifts(cellsWithShifts);
      },
      reject: () => {
        console.log('Удаление смен отменено пользователем');
      },
    });
  }

  // Выполнить удаление выбранных смен
  executeDeleteSelectedShifts(cellsWithShifts: SelectedCell[]) {
    cellsWithShifts.forEach((cell) => {
      const shiftToDelete: ShiftToDelete = {
        cellId: cell.cellId,
        userId: cell.userId,
        date: cell.date,
        shiftId: cell.shiftId,
      };

      this.shiftsToDelete.set(cell.cellId, shiftToDelete);

      // Убираем из других списков, если там была
      this.pendingShifts.delete(cell.cellId);
      this.shiftsToUpdate.delete(cell.cellId);
    });

    console.log('Отмечено выбранных смен на удаление:', cellsWithShifts.length);
  }

  // Получить код смены для ячейки (для отображения)
  getPendingShiftCode(cellId: string): string | null {
    const pending = this.pendingShifts.get(cellId);
    if (pending) {
      return pending.shiftTemplateCode + pending.shiftTypeCode;
    }
    return null;
  }

  // Проверить, есть ли назначение для ячейки
  hasPendingShift(cellId: string): boolean {
    return this.pendingShifts.has(cellId);
  }

  // Сохранить все назначенные смены
  applyShifts() {
    if (
      this.pendingShifts.size === 0 &&
      this.shiftsToUpdate.size === 0 &&
      this.shiftsToDelete.size === 0
    ) {
      console.warn('Нет изменений для сохранения');
      return;
    }

    // Если есть смены на обновление, показываем диалог подтверждения
    if (this.shiftsToUpdate.size > 0) {
      this.showUpdateConfirmation();
    } else {
      // Если только создание и удаление, применяем сразу
      this.executeApplyShifts();
    }
  }

  // Показать диалог подтверждения при обновлении существующих смен
  showUpdateConfirmation() {
    const updatesArray = Array.from(this.shiftsToUpdate.values());
    const affectedShiftsInfo = updatesArray
      .map((update) => {
        const userName = this.getUserName(update.userId);
        const formattedDate = new Date(update.date).toLocaleDateString(
          'ru-RU',
          {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
          }
        );
        return `• ${userName} - ${formattedDate}`;
      })
      .join('\n');

    const message = `Вы собираетесь изменить ${this.shiftsToUpdate.size} существующих смен:\n\n${affectedShiftsInfo}\n\nПродолжить?`;

    this.confirmationService.confirm({
      header: 'Подтверждение изменения смен',
      message: message,
      icon: 'pi pi-exclamation-triangle',
      acceptLabel: 'Да, изменить',
      rejectLabel: 'Отмена',
      acceptButtonStyleClass: 'p-button-warning',
      rejectButtonStyleClass: 'p-button-text',
      accept: () => {
        this.executeApplyShifts();
      },
      reject: () => {
        console.log('Применение изменений отменено пользователем');
      },
    });
  }

  // Выполнить применение изменений (DELETE + UPDATE + CREATE)
  executeApplyShifts() {
    this.savingShifts = true;

    // Массив промисов для параллельного выполнения
    const operations: any[] = [];

    // Функция для форматирования времени из HH:MM в HH:MM:SS
    const formatTime = (time: string): string => {
      if (!time) return '';
      // Если время уже в формате HH:MM:SS, возвращаем как есть
      if (time.includes(':') && time.split(':').length === 3) return time;
      // Если в формате HH:MM, добавляем секунды
      if (time.includes(':') && time.split(':').length === 2)
        return `${time}:00`;
      return time;
    };

    // 1. Удаляем смены если есть
    if (this.shiftsToDelete.size > 0) {
      const shiftsWithId = Array.from(this.shiftsToDelete.values()).filter(
        (shift) => shift.shiftId
      );

      shiftsWithId.forEach((shift) => {
        operations.push(this.shiftsService.delete(shift.shiftId!));
      });

      console.log('Удаление смен:', shiftsWithId.length);
    }

    // 2. Обновляем существующие смены если есть
    if (this.shiftsToUpdate.size > 0) {
      const shiftsToUpdateArray = Array.from(this.shiftsToUpdate.values()).map(
        (pending) => {
          const isFlexible = !this.selectedTemplate?.isFixedTime;

          return {
            id: pending.shiftId,
            shift: {
              user: pending.userId,
              shiftDate: pending.date,
              jobTitle: 'Global Service Desk Analyst',
              shiftType: pending.shiftTypeId.toString(),
              startTime: formatTime(
                isFlexible && this.flexibleStartTime
                  ? this.flexibleStartTime
                  : this.selectedTemplate?.startTime || ''
              ),
              endTime: formatTime(
                isFlexible && this.flexibleEndTime
                  ? this.flexibleEndTime
                  : this.selectedTemplate?.endTime || ''
              ),
              lunchStartTime: formatTime(
                isFlexible && this.flexibleLunchStartTime
                  ? this.flexibleLunchStartTime
                  : this.selectedTemplate?.lunchStartTime || ''
              ),
              lunchEndTime: formatTime(
                isFlexible && this.flexibleLunchEndTime
                  ? this.flexibleLunchEndTime
                  : this.selectedTemplate?.lunchEndTime || ''
              ),
              workHours: '',
              shiftTemplate: pending.shiftTemplateId.toString(),
              createdBy: '1932',
              isFixedTime: this.selectedTemplate?.isFixedTime || false,
            },
          };
        }
      );

      console.log('Обновление смен:', shiftsToUpdateArray.length);
      operations.push(this.shiftsService.updateBulk(shiftsToUpdateArray));
    }

    // 3. Создаем новые смены если есть
    if (this.pendingShifts.size > 0) {
      const shiftsToCreate = Array.from(this.pendingShifts.values()).map(
        (pending) => {
          const isFlexible = !this.selectedTemplate?.isFixedTime;

          return {
            user: pending.userId,
            shiftDate: pending.date,
            jobTitle: 'Global Service Desk Analyst',
            shiftType: pending.shiftTypeId.toString(),
            startTime: formatTime(
              isFlexible && this.flexibleStartTime
                ? this.flexibleStartTime
                : this.selectedTemplate?.startTime || ''
            ),
            endTime: formatTime(
              isFlexible && this.flexibleEndTime
                ? this.flexibleEndTime
                : this.selectedTemplate?.endTime || ''
            ),
            lunchStartTime: formatTime(
              isFlexible && this.flexibleLunchStartTime
                ? this.flexibleLunchStartTime
                : this.selectedTemplate?.lunchStartTime || ''
            ),
            lunchEndTime: formatTime(
              isFlexible && this.flexibleLunchEndTime
                ? this.flexibleLunchEndTime
                : this.selectedTemplate?.lunchEndTime || ''
            ),
            workHours: '',
            shiftTemplate: pending.shiftTemplateId.toString(),
            createdBy: '1932',
            isFixedTime: this.selectedTemplate?.isFixedTime || false,
          };
        }
      );

      console.log('Создание смен:', shiftsToCreate.length);
      operations.push(this.shiftsService.createBulk(shiftsToCreate));
    }

    // Выполняем все операции параллельно
    forkJoin(operations).subscribe({
      next: (results) => {
        console.log('Все изменения успешно применены:', results);
        this.savingShifts = false;
        this.pendingShifts.clear();
        this.shiftsToUpdate.clear();
        this.shiftsToDelete.clear();

        // Снимаем все выделения после успешного применения
        this.cellSelectionService.clearAllSelections();

        this.loadScheduleData(); // Перезагружаем календарь
      },
      error: (error) => {
        console.error('Ошибка при применении изменений:', error);
        this.savingShifts = false;
      },
    });
  }
}
