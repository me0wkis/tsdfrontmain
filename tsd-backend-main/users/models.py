from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
import re
from django.conf import settings

class Teams(models.Model):
    id = models.AutoField(primary_key=True)
    team_name = models.CharField(max_length=100)
    team_color = models.CharField(max_length=7)

    class Meta:
        managed = False
        db_table = 'tsd_teams'
        app_label = 'users'

class Desks(models.Model):
    id = models.AutoField(primary_key=True)
    desk_number = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'tsd_desks'
        app_label = 'users'


class UsersManager(models.Manager):
    """Кастомный менеджер для модели Users"""

    def get_queryset(self):
        return super().get_queryset()

    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


class GLPITitle(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    class Meta:
        db_table = 'glpi_usertitles'
        managed = False

class GLPIGroupsUsers(models.Model):
    id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField(db_column='users_id')
    group_id = models.IntegerField(db_column='groups_id')
    class Meta:
        db_table = 'glpi_groups_users'
        managed = False

class GLPIGroups(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, db_column='name')
    class Meta:
        db_table = 'glpi_groups'
        managed = False

class GLPICategory(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'glpi_usercategories'
        managed = False

class GLPIUsers(models.Model):
    id = models.IntegerField(primary_key=True)
    alias = models.CharField(max_length=100,db_column='name', unique=True)
    first_name = models.CharField(max_length=100, db_column='firstname')
    second_name = models.CharField(max_length=100, db_column='realname')
    user_title= models.IntegerField(db_column='usertitles_id')
   # user_category = models.IntegerField(db_column='usercategories_id')
    supervisor_name = models.IntegerField(db_column='users_id_supervisor')
    phone_number = models.CharField(max_length=20, db_column='phone')

    user_title = models.ForeignKey(
        GLPITitle,
        db_column='usertitles_id',
        to_field='id',
        on_delete=models.DO_NOTHING,
        related_name='employees',
        null=True
    )
    usercategories_id = models.ForeignKey(
        GLPICategory,
        db_column='usercategories_id',
        to_field='id',
        on_delete=models.DO_NOTHING,
        related_name='employees',
        null=True
    )
    class Meta:
        db_table = 'glpi_users'
        managed = False

class Users(models.Model):
    id = models.IntegerField(primary_key=True)
    alias = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=100)
    second_name = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    group_name = models.CharField(max_length=100)
    hiring_date = models.DateField()
    supervisor_name = models.CharField(max_length=100)
    email = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=20)
    desk = models.ForeignKey(Desks, on_delete=models.CASCADE, related_name='users')
    team = models.ForeignKey(Teams, on_delete=models.CASCADE, related_name='users')
    avatar_url = models.CharField(max_length=255)
    cc_abonent_id = models.CharField(max_length=10)
    is_active = models.IntegerField()
    objects = UsersManager()
    USERNAME_FIELD='alias'
    REQUIRED_FIELDS=['email']

    is_authenticated = True
    is_anonymous = False


    @property
    def is_manager(self):
        job_title = self.job_title.strip() if self.job_title else ""

        # Для отладки
        print(f"[MODEL is_manager] Checking for {self.alias}: '{job_title}'")

        # Проверяем по паттернам
        patterns = getattr(settings, 'MANAGER_JOB_TITLES_PATTERNS', [])
        for pattern in patterns:
            try:
                if re.match(pattern, job_title, re.IGNORECASE):
                    print(f"[MODEL is_manager] Matched pattern: {pattern}")
                    return True
            except re.error:
                continue

        # Проверяем точное совпадение
        manager_titles = getattr(settings, 'MANAGER_JOB_TITLES', [])
        if job_title in manager_titles:
            print(f"[MODEL is_manager] Exact match: {job_title}")
            return True

        print(f"[MODEL is_manager] No match - returning False")
        return False

    class Meta:
        managed = False
        db_table = 'tsd_users'
        app_label = 'users'