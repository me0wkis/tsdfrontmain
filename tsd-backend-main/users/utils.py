from rest_framework_simplejwt.tokens import RefreshToken


def create_jwt_token(user):
    """Создает JWT токен для кастомной модели Users"""
    print(f"\n[DEBUG TOKEN] Creating token for user: {user.alias}")
    print(f"[DEBUG TOKEN] User job_title: {user.job_title}")
    print(f"[DEBUG TOKEN] User is_manager property: {user.is_manager}")

    refresh = RefreshToken()

    # Обязательные поля
    refresh['user_id'] = user.id

    # Кастомные поля
    refresh['email'] = user.email
    refresh['first_name'] = user.first_name
    refresh['job_title'] = user.job_title or ''

    # ВАЖНО: Используем свойство is_manager
    # Убедитесь, что user.is_manager возвращает bool
    is_manager = user.is_manager
    print(f"[DEBUG TOKEN] Computed is_manager: {is_manager} (type: {type(is_manager)})")

    # Преобразуем в bool на всякий случай
    if not isinstance(is_manager, bool):
        is_manager = bool(is_manager)
        print(f"[DEBUG TOKEN] Converted to bool: {is_manager}")

    refresh['is_manager'] = is_manager

    # Копируем в access токен
    access = refresh.access_token
    access['user_id'] = user.id
    access['email'] = user.email
    access['first_name'] = user.first_name
    access['job_title'] = user.job_title or ''
    access['is_manager'] = is_manager

    print(f"[DEBUG TOKEN] Token created with is_manager={is_manager}")

    return {
        'refresh': str(refresh),
        'access': str(access),
    }