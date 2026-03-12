import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MainLayout } from '@core/layouts/main-layout/main-layout';

@Component({
  selector: 'app-management-page',
  standalone: true,
  imports: [CommonModule, RouterModule, MainLayout],
  templateUrl: './management-page.component.html',
})
export class ManagementPageComponent {
  menuItems = [
    {
      label: 'Shift Types',
      icon: 'pi pi-list',
      routerLink: '/management/shift-types',
    },
    {
      label: 'Shift Templates',
      icon: 'pi pi-clone',
      routerLink: '/management/shift-templates',
    },
    {
      label: 'Users',
      icon: 'pi pi-users',
      routerLink: '/management/users',
    },
  ];
}
