from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.core import management

def update_site_domain(sender, **kwargs):
    """
    Signal handler to update the site domain after migrations.
    """
    management.call_command('update_site')


class AuthProfilConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auth_profil'

    def ready(self):
        # Hubungkan signal 'post_migrate' dengan fungsi handler kita
        post_migrate.connect(update_site_domain, sender=self)