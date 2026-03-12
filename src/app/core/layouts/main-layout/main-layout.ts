import {
  Component,
  ContentChild,
  TemplateRef,
  ViewChild,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { Menu } from 'primeng/menu';
import { MenuModule } from 'primeng/menu';
import { MenuItem } from 'primeng/api';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-main',
  imports: [CommonModule, RouterModule, ButtonModule, MenuModule],
  templateUrl: './main-layout.html',
})
export class MainLayout {
  @ContentChild('sidebar') sidebarTemplate!: TemplateRef<any>;
  @ViewChild('userMenu') userMenu!: Menu;

  sidebarHidden = false;

  router = inject(Router);
  authService = inject(AuthService);

  get currentUser() {
    return this.authService.getCurrentUser();
  }

  get userInitials(): string {
    const user = this.currentUser;
    if (!user) return '?';
    const first = user.firstName?.[0] ?? '';
    const last = user.lastName?.[0] ?? '';
    return (first + last).toUpperCase() || '?';
  }

  get userFullName(): string {
    const user = this.currentUser;
    if (!user) return '';
    return (
      [user.firstName, user.lastName].filter(Boolean).join(' ') ||
      user.username ||
      ''
    );
  }

  userMenuItems: MenuItem[] = [
    {
      label: 'Выход',
      icon: 'pi pi-sign-out',
      command: () => this.authService.logout(),
    },
  ];

  toggleUserMenu(event: Event) {
    this.userMenu.toggle(event);
  }

  toggleSidebar() {
    this.sidebarHidden = !this.sidebarHidden;
  }

  navigateTo(route: string) {
    this.router.navigate([route]);
  }

  isActiveRoute(route: string): boolean {
    return this.router.url.includes(route);
  }
}
