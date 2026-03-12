import { Routes } from '@angular/router';
import { managementRoutes } from './features/management/management-routing.module';
// import { authGuard } from './core/guards/auth.guard'; // Отключено до готовности авторизации

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./features/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'auth/callback',
    loadComponent: () =>
      import('./features/login/callback.component').then(
        (m) => m.CallbackComponent,
      ),
  },
  {
    path: 'schedule',
    loadChildren: () =>
      import('./features/schedule/schedule-module').then(
        (m) => m.ScheduleModule,
      ),
    // canActivate: [authGuard], // Отключено
  },
  {
    path: 'calendar',
    loadComponent: () =>
      import('./features/calendar/calendar.component').then(
        (m) => m.CalendarComponent,
      ),
    // canActivate: [authGuard], // Отключено
  },
  {
    path: 'management',
    children: managementRoutes,
    // canActivate: [authGuard], // Отключено
  },
  {
    path: '',
    redirectTo: '/login',
    pathMatch: 'full',
  },
];
