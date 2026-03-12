import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

/**
 * Auth interceptor для session-based аутентификации
 * Добавляет withCredentials для отправки cookies с каждым запросом
 * При 401 ошибке редиректит на страницу логина
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);

  // Добавляем withCredentials ко всем запросам для отправки session cookie
  const clonedRequest = req.clone({
    withCredentials: true,
  });

  return next(clonedRequest).pipe(
    catchError((error: HttpErrorResponse) => {
      // При 401 ошибке (сессия истекла) редиректим на логин
      if (
        error.status === 401 &&
        !req.url.includes('/auth/login') &&
        !req.url.includes('/auth/me')
      ) {
        router.navigate(['/login']);
      }
      return throwError(() => error);
    }),
  );
};
