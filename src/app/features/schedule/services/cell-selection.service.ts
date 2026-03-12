import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

export interface SelectedCell {
  userId: string;
  date: string; // YYYY-MM-DD format
  shiftId?: number;
  cellId: string;
}

@Injectable({
  providedIn: 'root',
})
export class CellSelectionService {
  private selectedCellsSubject = new BehaviorSubject<SelectedCell[]>([]);
  public selectedCells$ = this.selectedCellsSubject.asObservable();

  // Выделенные пользователи (для ограничения рисования)
  private selectedUsersSubject = new BehaviorSubject<string[]>([]);
  public selectedUsers$ = this.selectedUsersSubject.asObservable();

  // Состояние рисования
  private isDrawing = false;
  private isRemovalDrawing = false;
  private wasDrawing = false;
  private actuallyDrawing = false;
  private drawingTimeoutId?: number;
  private startCell?: SelectedCell;

  constructor() {}

  // Получить текущие выбранные ячейки
  getSelectedCells(): SelectedCell[] {
    return this.selectedCellsSubject.value;
  }

  // Получить выбранных пользователей
  getSelectedUsers(): string[] {
    return this.selectedUsersSubject.value;
  }

  // Переключить выделение пользователя (клик по имени)
  toggleUserSelection(userId: string): void {
    const currentUsers = this.getSelectedUsers();
    const userIndex = currentUsers.indexOf(userId);

    let newUsers: string[];
    if (userIndex >= 0) {
      // Убираем пользователя из выделения
      newUsers = currentUsers.filter((id) => id !== userId);
    } else {
      // Добавляем пользователя к выделению
      newUsers = [...currentUsers, userId];
    }

    this.selectedUsersSubject.next(newUsers);
  }

  // Проверить, выбран ли пользователь
  isUserSelected(userId: string): boolean {
    return this.getSelectedUsers().includes(userId);
  }

  // Начать рисование (mousedown)
  startDrawing(cell: SelectedCell, isCtrlPressed: boolean = false): void {
    if (!this.canDrawOnCell(cell.userId)) {
      return;
    }

    this.isDrawing = true;
    this.isRemovalDrawing = isCtrlPressed;
    this.wasDrawing = false;
    this.actuallyDrawing = false;
    this.startCell = cell; // Сохраняем стартовую ячейку
  }

  // Обработать ячейку при рисовании
  private processDrawingCell(cell: SelectedCell): void {
    if (this.isRemovalDrawing) {
      this.removeCell(cell);
    } else {
      // Добавляем ячейку только если её нет в выделении
      const currentSelected = this.getSelectedCells();
      if (!currentSelected.some((c) => c.cellId === cell.cellId)) {
        this.selectedCellsSubject.next([...currentSelected, cell]);
      }
    }
  }

  // Продолжить рисование (mouseenter во время drawing)
  continueDrawing(cell: SelectedCell): void {
    if (!this.isDrawing || !this.canDrawOnCell(cell.userId)) {
      return;
    }

    // Если это первое движение мыши, обрабатываем стартовую ячейку
    if (!this.actuallyDrawing && this.startCell) {
      this.processDrawingCell(this.startCell);
      this.actuallyDrawing = true;
      this.wasDrawing = true;
    }

    // Обрабатываем текущую ячейку
    this.processDrawingCell(cell);
  }

  // Закончить рисование (mouseup)
  stopDrawing(): void {
    this.isDrawing = false;
    this.isRemovalDrawing = false;

    // Очищаем предыдущий timeout если есть
    if (this.drawingTimeoutId) {
      clearTimeout(this.drawingTimeoutId);
    }

    if (!this.actuallyDrawing) {
      // Простой клик - разрешаем обработку click сразу
      this.wasDrawing = false;
    } else {
      // Было рисование - блокируем click на короткое время
      this.drawingTimeoutId = window.setTimeout(() => {
        this.wasDrawing = false;
        this.drawingTimeoutId = undefined;
      }, 50);
    }

    this.actuallyDrawing = false;
    this.startCell = undefined; // Очищаем стартовую ячейку
  }

  // Обработка простого клика (toggle ячейки)
  handleCellClick(cell: SelectedCell): void {
    if (this.wasDrawing || !this.canDrawOnCell(cell.userId)) {
      return;
    }
    this.toggleCell(cell);
  }

  // Переключить состояние ячейки (выбрана/не выбрана)
  private toggleCell(cell: SelectedCell): void {
    const currentSelected = this.getSelectedCells();
    const existingIndex = currentSelected.findIndex(
      (c) => c.cellId === cell.cellId
    );

    const newSelected =
      existingIndex >= 0
        ? currentSelected.filter((c) => c.cellId !== cell.cellId)
        : [...currentSelected, cell];

    this.selectedCellsSubject.next(newSelected);
  }

  // Удалить ячейку из выделения
  private removeCell(cell: SelectedCell): void {
    const currentSelected = this.getSelectedCells();
    const newSelected = currentSelected.filter((c) => c.cellId !== cell.cellId);
    this.selectedCellsSubject.next(newSelected);
  }

  // Проверить, можно ли рисовать по ячейке данного пользователя
  canDrawOnCell(userId: string): boolean {
    const selectedUsers = this.getSelectedUsers();
    return selectedUsers.length === 0 || selectedUsers.includes(userId);
  }

  // Проверить, выбрана ли ячейка
  isCellSelected(cellId: string): boolean {
    return this.getSelectedCells().some((c) => c.cellId === cellId);
  }

  // Очистить выделение ячеек
  clearSelection(): void {
    this.selectedCellsSubject.next([]);
  }

  // Очистить выделение пользователей
  clearUserSelection(): void {
    this.selectedUsersSubject.next([]);
  }

  // Очистить все выделения
  clearAllSelections(): void {
    this.selectedCellsSubject.next([]);
    this.selectedUsersSubject.next([]);
  }

  // Получить состояние рисования
  isCurrentlyDrawing(): boolean {
    return this.isDrawing;
  }

  // Проверить, было ли недавно рисование
  wasRecentlyDrawing(): boolean {
    return this.wasDrawing;
  }

  // Очистка ресурсов (вызывается при уничтожении приложения)
  ngOnDestroy(): void {
    if (this.drawingTimeoutId) {
      clearTimeout(this.drawingTimeoutId);
    }
  }
}
