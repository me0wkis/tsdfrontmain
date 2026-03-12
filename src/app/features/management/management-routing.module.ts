import { Routes } from '@angular/router';
import { ManagementPageComponent } from './pages/management-page/management-page.component';
import { ShiftTypesManagementComponent } from './pages/shift-types-management/shift-types-management.component';
import { ShiftTemplatesManagementComponent } from './pages/shift-templates-management/shift-templates-management.component';
import { UsersManagementComponent } from './pages/users-management/users-management.component';

export const managementRoutes: Routes = [
  {
    path: '',
    component: ManagementPageComponent,
    children: [
      { path: '', redirectTo: 'users', pathMatch: 'full' },
      { path: 'shift-types', component: ShiftTypesManagementComponent },
      { path: 'shift-templates', component: ShiftTemplatesManagementComponent },
      { path: 'users', component: UsersManagementComponent },
    ],
  },
];
