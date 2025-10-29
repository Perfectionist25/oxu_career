from django.contrib import admin
from django.core.mail import send_mail
from django.utils.html import format_html
from django.conf import settings
from .models import ContactMessage

class ContactMessageAdmin(admin.ModelAdmin):
    """Админ-панель для сообщений обратной связи"""
    
    list_display = ('name', 'email', 'short_message', 'created_at', 'is_processed', 'processed_status')
    list_filter = ('is_processed', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('name', 'email', 'message', 'created_at', 'updated_at', 'message_preview')
    date_hierarchy = 'created_at'
    list_per_page = 20
    
    fieldsets = (
        ('Информация о отправителе', {
            'fields': ('name', 'email', 'created_at')
        }),
        ('Сообщение', {
            'fields': ('message_preview', 'message')
        }),
        ('Обработка сообщения', {
            'fields': ('is_processed', 'processed_at', 'admin_notes', 'updated_at')
        }),
    )
    
    actions = ['mark_as_processed', 'mark_as_unprocessed', 'export_emails', 'send_bulk_reply']

    def short_message(self, obj):
        """Сокращенное отображение сообщения"""
        if len(obj.message) > 100:
            return f"{obj.message[:100]}..."
        return obj.message
    short_message.short_description = "Сообщение"

    def message_preview(self, obj):
        """Предпросмотр сообщения с форматированием"""
        return format_html(
            '<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007cba; white-space: pre-wrap; font-family: Arial, sans-serif;">{}</div>',
            obj.message
        )
    message_preview.short_description = "Предпросмотр сообщения"

    def processed_status(self, obj):
        """Статус обработки с цветовым обозначением"""
        if obj.is_processed:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Обработано</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">● В ожидании</span>'
            )
    processed_status.short_description = "Статус"

    def mark_as_processed(self, request, queryset):
        """Пометить выбранные сообщения как обработанные"""
        updated = queryset.update(is_processed=True)
        self.message_user(request, f'{updated} сообщений помечены как обработанные.')
    mark_as_processed.short_description = "Пометить как обработанные"

    def mark_as_unprocessed(self, request, queryset):
        """Пометить выбранные сообщения как необработанные"""
        updated = queryset.update(is_processed=False)
        self.message_user(request, f'{updated} сообщений помечены как необработанные.')
    mark_as_unprocessed.short_description = "Пометить как необработанные"

    def export_emails(self, request, queryset):
        """Экспорт email адресов выбранных сообщений"""
        emails = list(queryset.values_list('email', flat=True).distinct())
        email_list = "\n".join(emails)
        
        # В реальном приложении здесь можно сгенерировать CSV файл
        self.message_user(request, f'Найдено {len(emails)} уникальных email адресов: {", ".join(emails[:5])}{"..." if len(emails) > 5 else ""}')
    export_emails.short_description = "Экспорт email адресов"

    def send_bulk_reply(self, request, queryset):
        """Массовая отправка ответов (заглушка для демонстрации)"""
        unprocessed = queryset.filter(is_processed=False)
        count = unprocessed.count()
        
        if count == 0:
            self.message_user(request, "Нет необработанных сообщений для ответа.", level='warning')
            return
        
        # В реальном приложении здесь была бы логика отправки email
        self.message_user(
            request, 
            f'Готово к отправке массового ответа на {count} сообщений. '
            'В реальной системе здесь будет отправка email.',
            level='success'
        )
    send_bulk_reply.short_description = "Отправить массовый ответ"

    def get_queryset(self, request):
        """Оптимизация запроса"""
        return super().get_queryset(request).select_related()

    def has_add_permission(self, request):
        """Запретить добавление новых сообщений через админку"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Разрешить удаление только суперпользователям"""
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        """Автоматическое обновление даты обработки"""
        if obj.is_processed and not obj.processed_at:
            from django.utils import timezone
            obj.processed_at = timezone.now()
        elif not obj.is_processed:
            obj.processed_at = None
            
        super().save_model(request, obj, form, change)

# Регистрация модели
admin.site.register(ContactMessage, ContactMessageAdmin)

# Дополнительно: если у вас есть другие модели в core, добавьте их здесь
# Например, для модели Settings (если есть)

# class SettingsAdmin(admin.ModelAdmin):
#     list_display = ('key', 'value', 'description')
#     list_editable = ('value',)
# 
# admin.site.register(Settings, SettingsAdmin)