import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { User, UsersResponse } from '@shared/models/users.model';
import {
  UsersService,
  UsersQueryParams,
} from '../../services/users-api.service';
import { TeamsApiService } from '../../services/teams-api.service';
import { Team } from '@shared/models/teams.model';

// PrimeNG modules
import { MessageService, ConfirmationService } from 'primeng/api';
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
  selector: 'app-users-management',
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
  templateUrl: './users-management.component.html',
  styleUrls: ['./users-management.component.css'],
})
export class UsersManagementComponent implements OnInit {
  users: User[] = [];
  selectedUsers: User[] = [];
  user: User = this.getEmptyUser();
  userDialog = false;
  submitted = false;
  loading = false;

  // Команды
  teams: Team[] = [];

  // Пагинация
  totalUsers = 0;
  currentPage = 0;
  rows = 10;
  sortField = 'first_name';
  sortOrder = 'asc';

  constructor(
    private usersService: UsersService,
    private teamsService: TeamsApiService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService
  ) {}

  ngOnInit() {
    this.loadUsers();
    this.loadTeams();
  }

  loadTeams() {
    this.teamsService.getAll().subscribe({
      next: (teams) => {
        this.teams = teams;
        console.log('Команды загружены:', teams);
      },
      error: (error) => {
        console.error('Ошибка загрузки команд:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Ошибка',
          detail: 'Не удалось загрузить команды',
        });
      },
    });
  }

  loadUsers() {
    this.loading = true;

    const params: UsersQueryParams = {
      limit: this.rows,
      offset: this.currentPage * this.rows,
      sort: `${this.sortField}-${this.sortOrder}`,
    };

    this.usersService.getPaginated(params).subscribe({
      next: (response: UsersResponse) => {
        this.users = response.results;
        this.totalUsers = response.count;
        this.loading = false;
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Ошибка',
          detail: 'Не удалось загрузить пользователей',
        });
        this.loading = false;
      },
    });
  }

  onPageChange(event: any) {
    this.currentPage = event.first / event.rows;
    this.rows = event.rows;

    // Обрабатываем сортировку если она есть
    if (event.sortField) {
      this.sortField = event.sortField;
      this.sortOrder = event.sortOrder === 1 ? 'asc' : 'desc';
    }

    this.loadUsers();
  }

  onSort(event: any) {
    // Этот метод может не понадобиться, так как сортировка обрабатывается в onPageChange
    // Но оставим для совместимости
    if (event.field) {
      this.sortField = event.field;
      this.sortOrder = event.order === 1 ? 'asc' : 'desc';
      this.currentPage = 0; // Reset to first page when sorting
      this.loadUsers();
    }
  }

  openNew() {
    this.user = this.getEmptyUser();
    this.submitted = false;
    this.userDialog = true;
  }

  editUser(user: User) {
    this.user = { ...user };
    this.userDialog = true;
  }

  deleteUser(user: User) {
    this.confirmationService.confirm({
      message: `Вы уверены, что хотите удалить пользователя ${user.firstName} ${user.secondName}?`,
      header: 'Подтверждение',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.usersService.delete(user.id).subscribe({
          next: () => {
            this.messageService.add({
              severity: 'success',
              summary: 'Успешно',
              detail: 'Пользователь удален',
            });
            this.loadUsers(); // Перезагружаем данные
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Ошибка',
              detail: 'Не удалось удалить пользователя',
            });
          },
        });
      },
    });
  }

  hideDialog() {
    this.userDialog = false;
    this.submitted = false;
  }

  saveUser() {
    this.submitted = true;

    if (this.user.firstName?.trim() && this.user.email?.trim()) {
      if (this.user.id) {
        this.usersService.update(this.user.id, this.user).subscribe({
          next: (updatedUser) => {
            this.messageService.add({
              severity: 'success',
              summary: 'Успешно',
              detail: 'Пользователь обновлен',
            });
            this.hideDialog();
            this.loadUsers(); // Перезагружаем данные
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Ошибка',
              detail: 'Не удалось обновить пользователя',
            });
          },
        });
      } else {
        this.usersService.create(this.user).subscribe({
          next: (newUser) => {
            this.messageService.add({
              severity: 'success',
              summary: 'Успешно',
              detail: 'Пользователь создан',
            });
            this.hideDialog();
            this.loadUsers(); // Перезагружаем данные
          },
          error: () => {
            this.messageService.add({
              severity: 'error',
              summary: 'Ошибка',
              detail: 'Не удалось создать пользователя',
            });
          },
        });
      }
    }
  }

  deleteSelectedUsers() {
    this.confirmationService.confirm({
      message: 'Вы уверены, что хотите удалить выбранных пользователей?',
      header: 'Подтверждение',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        let deleteCount = 0;
        const totalDeletes = this.selectedUsers.length;

        this.selectedUsers.forEach((user) => {
          this.usersService.delete(user.id).subscribe({
            next: () => {
              deleteCount++;
              if (deleteCount === totalDeletes) {
                this.messageService.add({
                  severity: 'success',
                  summary: 'Успешно',
                  detail: 'Пользователи удалены',
                });
                this.selectedUsers = [];
                this.loadUsers(); // Перезагружаем данные
              }
            },
            error: () => {
              deleteCount++;
              if (deleteCount === totalDeletes) {
                this.loadUsers(); // Перезагружаем данные даже если были ошибки
              }
            },
          });
        });
      },
    });
  }

  getTeamName(teamId: number | null | undefined): string {
    if (!teamId) return '-';
    const team = this.teams.find((t) => t.id === teamId);
    return team ? team.name : '-';
  }

  private getEmptyUser(): User {
    return {
      id: 0,
      alias: '',
      firstName: '',
      secondName: '',
      jobTitle: '',
      groupName: '',
      hiringDate: new Date().toISOString().split('T')[0],
      supervisorName: '',
      email: '',
      phoneNumber: '',
      desk: 0,
      team: 0,
      avatarUrl: null,
      isActive: true,
    };
  }
}
