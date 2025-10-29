from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()

class CVTemplate(models.Model):
    """Шаблоны резюме"""
    name = models.CharField(max_length=100, verbose_name="Название шаблона")
    description = models.TextField(verbose_name="Описание")
    thumbnail = models.ImageField(upload_to='cv_templates/', verbose_name="Превью")
    template_file = models.CharField(max_length=100, verbose_name="Файл шаблона")
    is_active = models.BooleanField(default=True, verbose_name="Активный")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Шаблон резюме"
        verbose_name_plural = "Шаблоны резюме"

    def __str__(self):
        return self.name

class CV(models.Model):
    """Модель резюме"""
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
        ('archived', 'В архиве'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    title = models.CharField(max_length=200, verbose_name="Название резюме")
    template = models.ForeignKey(CVTemplate, on_delete=models.SET_NULL, null=True, verbose_name="Шаблон")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")
    
    # Основная информация
    full_name = models.CharField(max_length=200, verbose_name="Полное имя")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    location = models.CharField(max_length=100, blank=True, verbose_name="Местоположение")
    photo = models.ImageField(upload_to='cv_photos/', null=True, blank=True, verbose_name="Фото")
    summary = models.TextField(blank=True, verbose_name="О себе")
    
    # Настройки
    show_photo = models.BooleanField(default=True, verbose_name="Показывать фото")
    show_email = models.BooleanField(default=True, verbose_name="Показывать email")
    show_phone = models.BooleanField(default=True, verbose_name="Показывать телефон")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Резюме"
        verbose_name_plural = "Резюме"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def get_absolute_url(self):
        return reverse('cvbuilder:cv_detail', kwargs={'pk': self.pk})

class Education(models.Model):
    """Образование"""
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='educations')
    institution = models.CharField(max_length=200, verbose_name="Учебное заведение")
    degree = models.CharField(max_length=100, verbose_name="Степень")
    field_of_study = models.CharField(max_length=100, verbose_name="Специальность")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(null=True, blank=True, verbose_name="Дата окончания")
    is_current = models.BooleanField(default=False, verbose_name="По настоящее время")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Образование"
        verbose_name_plural = "Образование"
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.institution} - {self.degree}"

class Experience(models.Model):
    """Опыт работы"""
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='experiences')
    company = models.CharField(max_length=200, verbose_name="Компания")
    position = models.CharField(max_length=200, verbose_name="Должность")
    location = models.CharField(max_length=100, verbose_name="Местоположение")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(null=True, blank=True, verbose_name="Дата окончания")
    is_current = models.BooleanField(default=False, verbose_name="По настоящее время")
    description = models.TextField(verbose_name="Описание обязанностей")

    class Meta:
        verbose_name = "Опыт работы"
        verbose_name_plural = "Опыт работы"
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.position} at {self.company}"

class Skill(models.Model):
    """Навыки"""
    SKILL_LEVELS = [
        ('beginner', 'Начальный'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый'),
        ('expert', 'Эксперт'),
    ]

    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100, verbose_name="Название навыка")
    level = models.CharField(max_length=20, choices=SKILL_LEVELS, verbose_name="Уровень")
    category = models.CharField(max_length=50, verbose_name="Категория")
    years_of_experience = models.IntegerField(default=0, verbose_name="Лет опыта")

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"

class Project(models.Model):
    """Проекты"""
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200, verbose_name="Название проекта")
    description = models.TextField(verbose_name="Описание проекта")
    technologies = models.CharField(max_length=300, verbose_name="Технологии")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(null=True, blank=True, verbose_name="Дата окончания")
    url = models.URLField(blank=True, verbose_name="Ссылка на проект")
    is_current = models.BooleanField(default=False, verbose_name="Текущий проект")

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ['-start_date']

    def __str__(self):
        return self.name

class Language(models.Model):
    """Языки"""
    LANGUAGE_LEVELS = [
        ('a1', 'A1 - Начальный'),
        ('a2', 'A2 - Элементарный'),
        ('b1', 'B1 - Средний'),
        ('b2', 'B2 - Выше среднего'),
        ('c1', 'C1 - Продвинутый'),
        ('c2', 'C2 - Владение в совершенстве'),
        ('native', 'Родной'),
    ]

    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='languages')
    name = models.CharField(max_length=50, verbose_name="Язык")
    level = models.CharField(max_length=20, choices=LANGUAGE_LEVELS, verbose_name="Уровень")

    class Meta:
        verbose_name = "Язык"
        verbose_name_plural = "Языки"

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"

class Certificate(models.Model):
    """Сертификаты"""
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='certificates')
    name = models.CharField(max_length=200, verbose_name="Название сертификата")
    issuing_organization = models.CharField(max_length=200, verbose_name="Организация")
    issue_date = models.DateField(verbose_name="Дата получения")
    expiration_date = models.DateField(null=True, blank=True, verbose_name="Срок действия")
    credential_id = models.CharField(max_length=100, blank=True, verbose_name="ID сертификата")
    credential_url = models.URLField(blank=True, verbose_name="Ссылка на сертификат")

    class Meta:
        verbose_name = "Сертификат"
        verbose_name_plural = "Сертификаты"
        ordering = ['-issue_date']

    def __str__(self):
        return self.name

class CVSettings(models.Model):
    """Настройки резюме"""
    cv = models.OneToOneField(CV, on_delete=models.CASCADE, related_name='settings')
    font_family = models.CharField(max_length=50, default='Arial', verbose_name="Шрифт")
    font_size = models.IntegerField(default=12, verbose_name="Размер шрифта")
    primary_color = models.CharField(max_length=7, default='#2c3e50', verbose_name="Основной цвет")
    secondary_color = models.CharField(max_length=7, default='#3498db', verbose_name="Вторичный цвет")
    margin = models.IntegerField(default=20, verbose_name="Отступы")
    line_spacing = models.DecimalField(max_digits=3, decimal_places=1, default=1.2, verbose_name="Межстрочный интервал")

    class Meta:
        verbose_name = "Настройка резюме"
        verbose_name_plural = "Настройки резюме"

    def __str__(self):
        return f"Настройки для {self.cv.title}"