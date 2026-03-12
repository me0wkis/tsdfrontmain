import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {
  Observable,
  BehaviorSubject,
  tap,
  catchError,
  of,
  switchMap,
} from 'rxjs';
import { Router } from '@angular/router';
import { API_BASE_URL, API_ENDPOINTS } from '../constants/api.constants';
import {
  LoginRequestDTO,
  LoginResponseDTO,
  UserAuthDTO,
  AuthMeResponseDTO,
} from '../DTO/auth.dto';

interface OIDCAuthResponse {
  auth_url: string;
  message: string;
}

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private currentUserSubject = new BehaviorSubject<UserAuthDTO | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();
  private authCheckInProgress = false;

  constructor(
    private http: HttpClient,
    private router: Router,
  ) {
    // Проверяем сессию при инициализации
    this.checkSession();
  }

  /**
   * Проверка активной сессии через API
   */
  private checkSession(): void {
    if (this.authCheckInProgress) return;
    this.authCheckInProgress = true;

    this.http
      .get<AuthMeResponseDTO>(`${API_BASE_URL}${API_ENDPOINTS.AUTH_ME}`, {
        withCredentials: true,
      })
      .pipe(
        catchError(() => {
          this.currentUserSubject.next(null);
          return of<AuthMeResponseDTO>({ authenticated: false });
        }),
      )
      .subscribe({
        next: (response) => {
          if (response.authenticated && response.user) {
            this.currentUserSubject.next(response.user);
          } else {
            this.currentUserSubject.next(null);
          }
          this.authCheckInProgress = false;
        },
        error: () => {
          this.authCheckInProgress = false;
        },
      });
  }

  /**
   * Ручной логин через username/password
   */
  login(username: string, password: string): Observable<LoginResponseDTO> {
    const loginData: LoginRequestDTO = { username, password };

    return this.http
      .post<LoginResponseDTO>(
        `${API_BASE_URL}${API_ENDPOINTS.AUTH_LOGIN}`,
        loginData,
        { withCredentials: true },
      )
      .pipe(
        tap((response) => {
          this.currentUserSubject.next(response.user);
        }),
      );
  }

  /**
   * Инициация OIDC логина через SLB ADFS
   * Backend вернет auth_url, произойдет редирект на ADFS
   * После успешного логина ADFS редиректит на /auth/callback (обрабатывается backend)
   * Backend создаст сессию и редиректит обратно на frontend (главную страницу)
   */
  initiateOIDCLogin(): void {
    // Запрашиваем auth_url с backend
    this.http
      .get<OIDCAuthResponse>(
        `${API_BASE_URL}${API_ENDPOINTS.OIDC_AUTHENTICATE}`,
        {
          withCredentials: true, // Важно для cookie/session
        },
      )
      .subscribe({
        next: (response) => {
          // Переходим на страницу логина ADFS
          window.location.href = response.auth_url;
        },
        error: (error) => {
          console.error('Failed to initiate OIDC login:', error);
          alert('Ошибка при инициализации входа');
        },
      });
  }

  /**
   * Logout - завершение сессии
   */
  logout(): void {
    this.http
      .get(`${API_BASE_URL}${API_ENDPOINTS.AUTH_LOGOUT}`, {
        withCredentials: true,
      })
      .subscribe({
        next: () => {
          this.currentUserSubject.next(null);
          this.router.navigate(['/login']);
        },
        error: () => {
          // Даже если запрос не удался, очищаем локальное состояние
          this.currentUserSubject.next(null);
          this.router.navigate(['/login']);
        },
      });
  }

  /**
   * Проверка авторизации (наличие активной сессии)
   */
  isAuthenticated(): boolean {
    return this.currentUserSubject.value !== null;
  }

  /**
   * Получение текущего пользователя
   */
  getCurrentUser(): UserAuthDTO | null {
    return this.currentUserSubject.value;
  }

  /**
   * Принудительное обновление информации о пользователе
   */
  refreshUserInfo(): Observable<UserAuthDTO | null> {
    return this.http
      .get<AuthMeResponseDTO>(`${API_BASE_URL}${API_ENDPOINTS.AUTH_ME}`, {
        withCredentials: true,
      })
      .pipe(
        tap((response) => {
          if (response.authenticated && response.user) {
            this.currentUserSubject.next(response.user);
          } else {
            this.currentUserSubject.next(null);
          }
        }),
        catchError(() => {
          this.currentUserSubject.next(null);
          return of(null);
        }),
        // Преобразуем AuthMeResponseDTO в UserAuthDTO | null
        tap(() => {}),
        // Возвращаем текущего пользователя
        switchMap(() => of(this.currentUserSubject.value)),
      );
  }
}
