import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { map, take } from 'rxjs';

/**
 * Guard проверяет наличие активной сессии через BehaviorSubject currentUser$.
 * При первом открытии страницы AuthService делает запрос к /auth/me при инициализации;
 * guard ждёт первого значения после того как isAuthenticated будет известен.
 *
 * Если сессия не найдена — редиректим на /login.
 */
export const authGuard = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Используем refreshUserInfo() чтобы гарантированно проверить сессию с сервера,
  // а не только из памяти (важно при F5 / прямом URL)
  return authService.refreshUserInfo().pipe(
    take(1),
    map((user) => {
      if (user) {
        return true;
      }
      return router.createUrlTree(['/login']);
    }),
  );
};
