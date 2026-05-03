from django.apps import AppConfig


class InventoryConfig(AppConfig):
    name = 'inventory'

    def ready(self):
        # IMPORTANTE: Esto registra las señales cuando arranca el servidor
        import inventory.models