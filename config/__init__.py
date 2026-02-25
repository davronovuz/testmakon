# Celery ni Django ishlaganda avtomatik yuklash
from .celery import app as celery_app

__all__ = ('celery_app',)
