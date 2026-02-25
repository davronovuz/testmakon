import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('testmakon')

# Django settings dan CELERY_ prefiksli barcha sozlamalarni oladi
app.config_from_object('django.conf:settings', namespace='CELERY')

# Barcha applardan tasks.py ni avtomatik topadi
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
