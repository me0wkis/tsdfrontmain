import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ShiftTypes } from '@shared/models/shifts.model';
import { ShiftTypesService } from '../../services/shift-types-api.service';
import { MessageService, ConfirmationService } from 'primeng/api';

// PrimeNG modules
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { RippleModule } from 'primeng/ripple';
import { ToolbarModule } from 'primeng/toolbar';
import { DialogModule } from 'primeng/dialog';
import { InputTextModule } from 'primeng/inputtext';
import { CheckboxModule } from 'primeng/checkbox';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ToastModule } from 'primeng/toast';
import { TagModule } from 'primeng/tag';
import { SelectModule } from 'primeng/select';

@Component({
  selector: 'app-shift-types-management',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    RippleModule,
    ToolbarModule,
    DialogModule,
    InputTextModule,
    CheckboxModule,
    ConfirmDialogModule,
    ToastModule,
    TagModule,
    SelectModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './shift-types-management.component.html',
  styleUrls: ['./shift-types-management.component.css'],
})
export class ShiftTypesManagementComponent implements OnInit {
  shiftTypes: ShiftTypes[] = [];
  selectedShiftTypes: ShiftTypes[] = [];
  shiftType: ShiftTypes = this.getEmptyShiftType();
  shiftTypeDialog = false;
  submitted = false;
  loading = false;

  constructor(
    private shiftTypesService: ShiftTypesService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.loadShiftTypes();
  }

  loadShiftTypes() {
    this.loading = true;
    this.shiftTypesService.getAll().subscribe({
      next: (data) => {
        this.shiftTypes = data;
        this.loading = false;
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Ошибка',
          detail: 'Не удалось загрузить типы смен',
        });
        this.loading = false;
      },
    });
  }

  openNew() {
    this.shiftType = this.getEmptyShiftType();
    this.submitted = false;
    this.shiftTypeDialog = true;
  }

  editShiftType(shiftType: ShiftTypes) {
    this.shiftType = { ...shiftType };
    this.shiftTypeDialog = true;
  }

  deleteShiftType(shiftType: ShiftTypes) {
    this.confirmationService.confirm({
      message: `Вы уверены, что хотите удалить тип смены "${shiftType.name}"?`,
      header: 'Подтверждение',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.shiftTypesService.delete(shiftType.id).subscribe({
          next: () => {
            this.shiftTypes = this.shiftTypes.filter(
              (st) => st.id !== shiftType.id
            );
            this.messageService.add({
              severity: 'success',
              summary: 'Успешно',
              detail: 'Тип смены удален',
            });
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Ошибка',
              detail: 'Не удалось удалить тип смены',
            });
          },
        });
      },
    });
  }

  hideDialog() {
    this.shiftTypeDialog = false;
    this.submitted = false;
  }

  saveShiftType() {
    this.submitted = true;

    if (this.shiftType.name?.trim() && this.shiftType.code?.trim()) {
      if (this.shiftType.id) {
        this.shiftTypesService
          .update(this.shiftType.id, this.shiftType)
          .subscribe({
            next: (updatedShiftType) => {
              const index = this.shiftTypes.findIndex(
                (st) => st.id === updatedShiftType.id
              );
              this.shiftTypes[index] = updatedShiftType;
              this.messageService.add({
                severity: 'success',
                summary: 'Успешно',
                detail: 'Тип смены обновлен',
              });
              this.hideDialog();
            },
            error: () => {
              this.messageService.add({
                severity: 'error',
                summary: 'Ошибка',
                detail: 'Не удалось обновить тип смены',
              });
            },
          });
      } else {
        this.shiftTypesService.create(this.shiftType).subscribe({
          next: (newShiftType) => {
            this.shiftTypes.push(newShiftType);
            this.messageService.add({
              severity: 'success',
              summary: 'Успешно',
              detail: 'Тип смены создан',
            });
            this.hideDialog();
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Ошибка',
              detail: 'Не удалось создать тип смены',
            });
          },
        });
      }
    }
  }

  deleteSelectedShiftTypes() {
    this.confirmationService.confirm({
      message: 'Вы уверены, что хотите удалить выбранные типы смен?',
      header: 'Подтверждение',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.selectedShiftTypes.forEach((shiftType) => {
          this.shiftTypesService.delete(shiftType.id).subscribe({
            next: () => {
              this.shiftTypes = this.shiftTypes.filter(
                (st) => st.id !== shiftType.id
              );
            },
          });
        });

        this.messageService.add({
          severity: 'success',
          summary: 'Успешно',
          detail: 'Типы смен удалены',
        });
        this.selectedShiftTypes = [];
      },
    });
  }

  private getEmptyShiftType(): ShiftTypes {
    return {
      id: 0,
      name: '',
      code: '',
      isWorkShift: true,
    };
  }
}
