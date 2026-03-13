# Настройка Reverse Proxy для TSD Backend

## Изменения в проекте

Для работы с reverse proxy (Apache) были внесены следующие изменения:

### 1. Настройки в `.env`

Добавлены следующие переменные окружения:

```env
# Django settings
DEBUG=True                    # Для продакшена установите False
SECRET_KEY=your-secret-key    # Сгенерируйте уникальный ключ для продакшена

# Allowed hosts (comma-separated, без пробелов)
ALLOWED_HOSTS=localhost,127.0.0.1,tsdp.ru,www.tsdp.ru

# Reverse proxy settings
USE_HTTPS_PROXY=True          # True если используется HTTPS через прокси
USE_X_FORWARDED_HOST=True     # Обязательно True для reverse proxy
USE_X_FORWARDED_PORT=True     # True для корректной работы портов

# CSRF trusted origins (с протоколом, без пробелов)
CSRF_TRUSTED_ORIGINS=https://tsdp.ru,https://www.tsdp.ru

# CORS settings
CORS_ALLOW_ALL=False          # Для продакшена лучше False
CORS_ALLOWED_ORIGINS=https://tsdp.ru,https://www.tsdp.ru
```

### 2. Изменения в `settings.py`

- `DEBUG` теперь читается из переменной окружения
- `SECRET_KEY` читается из переменной окружения
- `ALLOWED_HOSTS` читается из переменной окружения (список через запятую)
- Добавлены настройки для работы с HTTPS через прокси
- Настроены заголовки `X-Forwarded-*`
- Добавлены `CSRF_TRUSTED_ORIGINS` для безопасности
- CORS настраивается через переменные окружения

## Настройка Apache

### 1. Установка Apache и необходимых модулей

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install apache2

# Включите необходимые модули
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
sudo a2enmod ssl
sudo a2enmod rewrite
sudo a2enmod expires

# Перезапустите Apache
sudo systemctl restart apache2
```

### 2. Конфигурация Apache

Используйте файл `apache-example.conf` как основу:

**Для Ubuntu/Debian:**

```bash
# Скопируйте конфигурацию
sudo cp apache-example.conf /etc/apache2/sites-available/tsdp.conf

# Активируйте сайт
sudo a2ensite tsdp.conf

# Отключите дефолтный сайт (опционально)
sudo a2dissite 000-default.conf

# Проверьте конфигурацию
sudo apache2ctl configtest

# Перезапустите Apache
sudo systemctl restart apache2
```


### 4. Настройка Firewall

**Ubuntu (ufw):**

```bash
sudo ufw allow 'Apache Full'
sudo ufw enable
```

### 5. Структура URL

После настройки reverse proxy:

- **Внешний URL**: `https://tsdp.ru/api/...`
- **Внутренний URL**: `http://127.0.0.1:8000/api/...`

Например:

- `https://tsdp.ru/api/portal/users/` → `http://127.0.0.1:8000/api/portal/users/`
- `https://tsdp.ru/api/swagger/` → `http://127.0.0.1:8000/api/swagger/`

## Запуск Django приложения

### 1. Для разработки

```bash
python manage.py runserver 127.0.0.1:8000
```

### 2. Для продакшена (используйте Gunicorn или uWSGI)

**С Gunicorn:**

```bash
# Установите gunicorn
pip install gunicorn

# Запустите
gunicorn tsdp_backend.wsgi:application --bind 127.0.0.1:8000 --workers 4
```

**Или создайте systemd service:**

```bash
sudo nano /etc/systemd/system/tsdp-backend.service
```

```ini
[Unit]
Description=TSD Backend Django Application
After=network.target

[Service]
Type=notify
User=www-data     
Group=www-data
WorkingDirectory=/path/to/tsd-backend
Environment="PATH=/path/to/tsd-backend/venv/bin"
ExecStart=/path/to/tsd-backend/venv/bin/gunicorn tsdp_backend.wsgi:application --bind 127.0.0.1:8000 --workers 4

[Install]
WantedBy=multi-user.target
```

```bash
# Включите и запустите сервис
sudo systemctl daemon-reload
sudo systemctl enable tsdp-backend
sudo systemctl start tsdp-backend
sudo systemctl status tsdp-backend
```

## Проверка работы

1. **Проверьте статус Django:**

   ```bash
   curl http://127.0.0.1:8000/api/swagger/
   ```

2. **Проверьте через Apache:**

   ```bash
   curl http://tsdp.ru/api/swagger/
   # или с HTTPS:
   curl https://tsdp.ru/api/swagger/
   ```

3. **Проверьте логи Apache:**

   **Ubuntu/Debian:**

   ```bash
   sudo tail -f /var/log/apache2/tsdp-access.log
   sudo tail -f /var/log/apache2/tsdp-error.log
   ```

   **CentOS/RHEL:**

   ```bash
   sudo tail -f /var/log/httpd/tsdp-access.log
   sudo tail -f /var/log/httpd/tsdp-error.log
   ```

4. **Проверьте статус Apache:**
   ```bash
   sudo systemctl status apache2  # Ubuntu/Debian
   sudo systemctl status httpd    # CentOS/RHEL
   ```

## Важные замечания для продакшена

1. ✅ Установите `DEBUG=False` в `.env`
2. ✅ Сгенерируйте новый `SECRET_KEY`
3. ✅ Настройте SSL сертификат
4. ✅ Используйте gunicorn/uWSGI вместо runserver
5. ✅ Настройте файрвол (откройте порты 80 и 443)
6. ✅ Ограничьте `CORS_ALLOWED_ORIGINS` только нужными доменами
7. ✅ Настройте регулярные бэкапы базы данных
8. ✅ Настройте мониторинг и логирование
9. ✅ Для CentOS/RHEL: настройте SELinux правильно

## Генерация нового SECRET_KEY

```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Скопируйте полученный ключ в `.env` файл.

## Возможные проблемы и решения

### Apache не может подключиться к Django (502 Bad Gateway)

1. **Проверьте, запущен ли Django:**

   ```bash
   curl http://127.0.0.1:8000/api/
   ```

2. **Проверьте SELinux (CentOS/RHEL):**

   ```bash
   sudo setsebool -P httpd_can_network_connect 1
   ```

3. **Проверьте логи Apache** для подробностей ошибки

### CSRF token errors

Убедитесь что:

- `USE_X_FORWARDED_HOST=True` в `.env`
- `CSRF_TRUSTED_ORIGINS` содержит ваш домен с протоколом (`https://tsdp.ru`)
- В Apache настроены заголовки `X-Forwarded-Proto` и `X-Forwarded-Host`

### CORS errors

Убедитесь что:

- `CORS_ALLOWED_ORIGINS` содержит ваш домен
- Или `CORS_ALLOW_ALL=True` для тестирования (не рекомендуется для продакшена)
