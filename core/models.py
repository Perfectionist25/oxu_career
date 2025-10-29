# core/models.py
from django.db import models

class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новое'),
        ('in_progress', 'В обработке'),
        ('completed', 'Завершено'),
        ('spam', 'Спам'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Имя")
    email = models.EmailField(verbose_name="Email")
    subject = models.CharField(max_length=255, blank=True, verbose_name="Тема")
    message = models.TextField(verbose_name="Сообщение")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='new',
        verbose_name="Статус"
    )
    is_processed = models.BooleanField(default=False, verbose_name="Обработано")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата обработки")
    admin_notes = models.TextField(blank=True, verbose_name="Заметки администратора")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP адрес")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Сообщение обратной связи"
        verbose_name_plural = "Сообщения обратной связи"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['is_processed']),
        ]

    def __str__(self):
        return f"Сообщение от {self.name} ({self.email})"

    def get_status_color(self):
        """Цвет статуса для админки"""
        colors = {
            'new': 'orange',
            'in_progress': 'blue', 
            'completed': 'green',
            'spam': 'red',
        }
        return colors.get(self.status, 'gray')