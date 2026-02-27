import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('testmakon')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Har kuni ertalab 8:00 da (Toshkent vaqti)
app.conf.beat_schedule = {
    'daily-study-reminders': {
        'task': 'ai_core.tasks.send_daily_study_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    'warm-leaderboard-cache': {
        'task': 'leaderboard.tasks.warm_leaderboard_cache',
        'schedule': crontab(minute='*/10'),
    },
    'process-matchmaking': {
        'task': 'competitions.tasks.process_matchmaking_queue',
        'schedule': 5.0,  # har 5 soniya
    },
}
app.conf.timezone = 'Asia/Tashkent'


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
