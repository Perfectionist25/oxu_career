from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class EmployersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'employers'
    verbose_name = _('Employers')
    
    def ready(self):
        import employers.signals