from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'
    verbose_name = _('Jobs')
    
    def ready(self):
        import jobs.signals