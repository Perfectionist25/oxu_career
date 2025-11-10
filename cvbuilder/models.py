from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

User = get_user_model()


class CVTemplate(models.Model):
    """Шаблоны резюме"""

    name = models.CharField(max_length=100, verbose_name="Название шаблона")
    thumbnail = models.ImageField(upload_to="cv_templates/", verbose_name="Превью")
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
        ("draft", "Черновик"),
        ("published", "Опубликовано"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    title = models.CharField(
        max_length=200, verbose_name="Название резюме", default="Мое резюме"
    )
    template = models.ForeignKey(
        CVTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Шаблон",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name="Статус"
    )

    # Основная информация (как в HH)
    full_name = models.CharField(max_length=200, verbose_name="Полное имя")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    location = models.CharField(max_length=100, verbose_name="Город")
    salary_expectation = models.IntegerField(
        null=True, blank=True, verbose_name="Зарплатные ожидания"
    )
    summary = models.TextField(verbose_name="О себе")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Резюме"
        verbose_name_plural = "Резюме"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def get_absolute_url(self):
        return reverse("cvbuilder:cv_detail", kwargs={"pk": self.pk})


class Experience(models.Model):
    """Опыт работы (основной раздел как в HH)"""

    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name="experiences")
    company = models.CharField(max_length=200, verbose_name="Компания")
    position = models.CharField(max_length=200, verbose_name="Должность")
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(null=True, blank=True, verbose_name="Дата окончания")
    is_current = models.BooleanField(default=False, verbose_name="По настоящее время")
    description = models.TextField(verbose_name="Обязанности и достижения")

    class Meta:
        verbose_name = "Опыт работы"
        verbose_name_plural = "Опыт работы"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.position} в {self.company}"


class Education(models.Model):
    """Образование"""

    DEGREE_CHOICES = [
        ("secondary", "Среднее"),
        ("specialized_secondary", "Среднее специальное"),
        ("bachelor", "Бакалавр"),
        ("master", "Магистр"),
        ("phd", "Кандидат наук"),
        ("doctor", "Доктор наук"),
    ]

    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name="educations")
    institution = models.CharField(max_length=200, verbose_name="Учебное заведение")
    degree = models.CharField(
        max_length=50, choices=DEGREE_CHOICES, verbose_name="Степень"
    )
    field_of_study = models.CharField(max_length=100, verbose_name="Специальность")
    graduation_year = models.IntegerField(verbose_name="Год окончания")

    class Meta:
        verbose_name = "Образование"
        verbose_name_plural = "Образование"
        ordering = ["-graduation_year"]

    def __str__(self):
        return f"{self.institution} - {self.field_of_study}"


class Skill(models.Model):
    """Навыки"""

    SKILL_LEVELS = [
        ("beginner", "Начальный"),
        ("intermediate", "Средний"),
        ("advanced", "Продвинутый"),
        ("expert", "Эксперт"),
    ]

    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100, verbose_name="Навык")
    level = models.CharField(
        max_length=20, choices=SKILL_LEVELS, verbose_name="Уровень"
    )

    class Meta:
        verbose_name = "Навык"
        verbose_name_plural = "Навыки"

    def __str__(self):
        return self.name


class Language(models.Model):
    """Языки"""

    LANGUAGE_LEVELS = [
        ("a1", "A1 - Начальный"),
        ("a2", "A2 - Элементарный"),
        ("b1", "B1 - Средний"),
        ("b2", "B2 - Выше среднего"),
        ("c1", "C1 - Продвинутый"),
        ("c2", "C2 - В совершенстве"),
        ("native", "Родной"),
    ]

    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name="languages")
    name = models.CharField(max_length=50, verbose_name="Язык")
    level = models.CharField(
        max_length=20, choices=LANGUAGE_LEVELS, verbose_name="Уровень"
    )

    class Meta:
        verbose_name = "Язык"
        verbose_name_plural = "Языки"

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"
