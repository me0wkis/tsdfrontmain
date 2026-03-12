import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '@core/services/auth.service';

/**
 * Callback компонент для OIDC flow
 *
 * По документу backend должен обрабатывать /auth/callback сам:
 * 1. ADFS редиректит на /auth/callback?code=xxx
 * 2. Backend получает code, обменивает на token
 * 3. Backend создает session cookie (httpOnly)
 * 4. Backend редиректит на главную страницу (/)
 *
 * Этот компонент нужен только в случае, если:
 * - Backend уже обработал callback и установил cookie
 * - Пользователь попал на этот роут после редиректа
 * - Нужно проверить сессию и перенаправить на главную
 */
@Component({
  selector: 'app-callback',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="callback-container">
      <div class="callback-content">
        <div class="loader"></div>
        <h2>Обработка входа...</h2>
        <p *ngIf="errorMessage" class="error">{{ errorMessage }}</p>
      </div>
    </div>
  `,
  styles: [
    `
      .callback-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      }

      .callback-content {
        text-align: center;
        background: white;
        padding: 3rem;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
      }

      .loader {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: 0 auto 1.5rem;
      }

      @keyframes spin {
        0% {
          transform: rotate(0deg);
        }
        100% {
          transform: rotate(360deg);
        }
      }

      h2 {
        color: #333;
        margin: 0 0 0.5rem;
      }

      p {
        color: #666;
        margin: 0;
      }

      .error {
        color: #d32f2f;
        margin-top: 1rem;
      }
    `,
  ],
})
export class CallbackComponent implements OnInit {
  errorMessage = '';
  private authService = inject(AuthService);
  private router = inject(Router);

  ngOnInit(): void {
    // Backend уже должен был обработать callback и установить session cookie
    // Проверяем наличие сессии и редиректим
    this.checkSessionAndRedirect();
  }

  private checkSessionAndRedirect(): void {
    // Даем backend время на установку cookie (если редирект произошел быстро)
    setTimeout(() => {
      this.authService.refreshUserInfo().subscribe({
        next: (user) => {
          if (user) {
            // Сессия активна, переходим на главную страницу
            this.router.navigate(['/schedule']);
          } else {
            // Сессия не найдена - возможно backend не установил cookie
            this.errorMessage = 'Ошибка авторизации. Попробуйте снова.';
            setTimeout(() => {
              this.router.navigate(['/login']);
            }, 2000);
          }
        },
        error: () => {
          this.errorMessage = 'Ошибка проверки сессии.';
          setTimeout(() => {
            this.router.navigate(['/login']);
          }, 2000);
        },
      });
    }, 500);
  }
}
