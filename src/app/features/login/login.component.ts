import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '@core/services/auth.service';
import { LoginResponseDTO } from '@core/DTO/auth.dto';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
})
export class LoginComponent implements OnInit {
  username: string = '';
  password: string = '';
  errorMessage: string = '';
  isLoading: boolean = false;

  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  ngOnInit(): void {
    // Если пришли с ?oidc=1 — backend завершил ADFS flow и установил session cookie.
    // Проверяем сессию и переходим на /schedule.
    const oidcParam = this.route.snapshot.queryParamMap.get('oidc');
    if (oidcParam === '1') {
      this.isLoading = true;
      this.authService.refreshUserInfo().subscribe({
        next: (user) => {
          if (user) {
            this.router.navigate(['/schedule']);
          } else {
            this.isLoading = false;
            this.errorMessage = 'Ошибка авторизации. Попробуйте снова.';
          }
        },
        error: () => {
          this.isLoading = false;
          this.errorMessage = 'Ошибка проверки сессии.';
        },
      });
    }
  }

  onLogin(): void {
    if (!this.username || !this.password) {
      this.errorMessage = 'Пожалуйста, заполните все поля';
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';

    this.authService.login(this.username, this.password).subscribe({
      next: (response: LoginResponseDTO) => {
        this.isLoading = false;
        this.router.navigate(['/schedule']);
      },
      error: (error: any) => {
        this.isLoading = false;
        this.errorMessage = 'Неверный логин или пароль';
        console.error('Login error:', error);
      },
    });
  }

  onAutoLogin(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.authService.initiateOIDCLogin();
  }
}
