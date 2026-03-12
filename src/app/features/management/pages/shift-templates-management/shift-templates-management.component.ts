import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ShiftTemplates, ShiftTypes } from '../../../../shared/models/shifts.model';
import { ShiftTemplatesService } from '../../services/shift-templates-api.service';
import { ShiftTypesService } from '../../services/shift-types-api.service';
import { MessageService, ConfirmationService } from 'primeng/api';
import { forkJoin } from 'rxjs';

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
import { BadgeModule } from 'primeng/badge';

@Component({
  selector: 'app-shift-templates-management',
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
    BadgeModule,
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './shift-templates-management.component.html',
  styleUrls: ['./shift-templates-management.component.css'],
})
export class ShiftTemplatesManagementComponent implements OnInit {
  shiftTemplates: ShiftTemplates[] = [];
  selectedShiftTemplates: ShiftTemplates[] = [];
  shiftTemplate: ShiftTemplates = this.getEmptyShiftTemplate();
  shiftTemplateDialog = false;
  submitted = false;
  loading = false;
  
  // Для группировки
  shiftTypes: ShiftTypes[] = [];
  shiftTypesMap: Map<number, string> = new Map();
  groupedShiftTemplates: any[] = [];

  private shiftTemplatesService = inject(ShiftTemplatesService);
  private shiftTypesService = inject(ShiftTypesService);
  private messageService = inject(MessageService);
  private confirmationService = inject(ConfirmationService);

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    
    // Загружаем одновременно шаблоны смен и типы смен
    forkJoin({
      shiftTemplates: this.shiftTemplatesService.getAll(),
      shiftTypes: this.shiftTypesService.getAll()
    }).subscribe({
      next: (data) => {
        this.shiftTemplates = data.shiftTemplates;
        this.shiftTypes = data.shiftTypes;
        
        // Создаем map для быстрого поиска названий типов смен
        this.shiftTypesMap = new Map();
        this.shiftTypes.forEach(type => {
          this.shiftTypesMap.set(type.id, type.name);
        });
        
        // Группируем данные
        this.groupShiftTemplatesByType();
        this.loading = false;
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Ошибка',
          detail: 'Не удалось загрузить данные',
        });
        this.loading = false;
      },
    });
  }

  loadShiftTemplates() {
    this.loading = true;
    this.shiftTemplatesService.getAll().subscribe({
      next: (data) => {
        this.shiftTemplates = data;
        this.groupShiftTemplatesByType();
        this.loading = false;
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Ошибка',
          detail: 'Не удалось загрузить шаблоны смен',
        });
        this.loading = false;
      },
    });
  }

  groupShiftTemplatesByType() {
    // Группируем шаблоны по типам смен
    const grouped = this.shiftTemplates.reduce((acc, template) => {
      const shiftTypeName = this.shiftTypesMap.get(template.shiftType) || 'Неизвестный тип';
      
      if (!acc[shiftTypeName]) {
        acc[shiftTypeName] = [];
      }
      
      acc[shiftTypeName].push(template);
      return acc;
    }, {} as { [key: string]: ShiftTemplates[] });

    // Преобразуем в формат для PrimeNG RowGroup
    this.groupedShiftTemplates = Object.keys(grouped).map(typeName => ({
      shiftTypeName: typeName,
      templates: grouped[typeName]
    }));
  }

  getShiftTypeName(shiftTypeId: number): string {
    return this.shiftTypesMap.get(shiftTypeId) || 'Неизвестный тип';
  }

  getShiftTypeCount(shiftTypeId: number): number {
    return this.shiftTemplates.filter(st => st.shiftType === shiftTypeId).length;
  }

  openNew() {
    this.shiftTemplate = this.getEmptyShiftTemplate();
    this.submitted = false;
    this.shiftTemplateDialog = true;
  }

  editShiftTemplate(shiftTemplate: ShiftTemplates) {
    this.shiftTemplate = { ...shiftTemplate };
    this.shiftTemplateDialog = true;
  }

  deleteShiftTemplate(shiftTemplate: ShiftTemplates) {
    this.confirmationService.confirm({
      message: `Вы уверены, что хотите удалить шаблон смены "${shiftTemplate.code}"?`,
      header: 'Подтверждение',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.shiftTemplatesService.delete(shiftTemplate.id).subscribe({
          next: () => {
            this.shiftTemplates = this.shiftTemplates.filter(
              (st) => st.id !== shiftTemplate.id
            );
            this.groupShiftTemplatesByType(); // Перегруппировываем данные
            this.messageService.add({
              severity: 'success',
              summary: 'Успешно',
              detail: 'Шаблон смены удален',
            });
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Ошибка',
              detail: 'Не удалось удалить шаблон смены',
            });
          },
        });
      },
    });
  }

  hideDialog() {
    this.shiftTemplateDialog = false;
    this.submitted = false;
  }

  saveShiftTemplate() {
    this.submitted = true;

    if (
      this.shiftTemplate.code?.trim() &&
      this.shiftTemplate.description?.trim()
    ) {
      if (this.shiftTemplate.id) {
        this.shiftTemplatesService
          .update(this.shiftTemplate.id, this.shiftTemplate)
          .subscribe({
            next: (updatedShiftTemplate) => {
              const index = this.shiftTemplates.findIndex(
                (st) => st.id === updatedShiftTemplate.id
              );
              this.shiftTemplates[index] = updatedShiftTemplate;
              this.groupShiftTemplatesByType(); // Перегруппировываем данные
              this.messageService.add({
                severity: 'success',
                summary: 'Успешно',
                detail: 'Шаблон смены обновлен',
              });
              this.hideDialog();
            },
            error: () => {
              this.messageService.add({
                severity: 'error',
                summary: 'Ошибка',
                detail: 'Не удалось обновить шаблон смены',
              });
            },
          });
      } else {
        this.shiftTemplatesService.create(this.shiftTemplate).subscribe({
          next: (newShiftTemplate) => {
            this.shiftTemplates.push(newShiftTemplate);
            this.groupShiftTemplatesByType(); // Перегруппировываем данные
            this.messageService.add({
              severity: 'success',
              summary: 'Успешно',
              detail: 'Шаблон смены создан',
            });
            this.hideDialog();
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Ошибка',
              detail: 'Не удалось создать шаблон смены',
            });
          },
        });
      }
    }
  }

  deleteSelectedShiftTemplates() {
    this.confirmationService.confirm({
      message: 'Вы уверены, что хотите удалить выбранные шаблоны смен?',
      header: 'Подтверждение',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.selectedShiftTemplates.forEach((shiftTemplate) => {
          this.shiftTemplatesService.delete(shiftTemplate.id).subscribe({
            next: () => {
              this.shiftTemplates = this.shiftTemplates.filter(
                (st) => st.id !== shiftTemplate.id
              );
            },
          });
        });

        this.messageService.add({
          severity: 'success',
          summary: 'Успешно',
          detail: 'Шаблоны смен удалены',
        });
        this.selectedShiftTemplates = [];
      },
    });
  }

  private getEmptyShiftTemplate(): ShiftTemplates {
    return {
      id: 0,
      code: '',
      description: '',
      isFixedTime: false,
      startTime: '',
      endTime: '',
      lunchStartTime: '',
      lunchEndTime: '',
      shiftType: 0,
      icon: '',
      allowedRoles: '',
      isActive: true,
      isOffice: false,
    };
  }
}
