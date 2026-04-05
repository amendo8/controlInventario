from django.apps import AppConfig
from django_tailwind.apps import DjangoTailwindAppConfig


class ThemeConfig(DjangoTailwindAppConfig):
    name = 'theme'
