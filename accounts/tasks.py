from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id):
    """Ro'yxatdan o'tgandan keyin xush kelibsiz emaili."""
    try:
        from accounts.models import User
        user = User.objects.get(id=user_id)
        send_mail(
            subject="TestMakon'ga xush kelibsiz!",
            message=f"Salom {user.first_name}, platformamizga xush kelibsiz!",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
        logger.info(f"Welcome email yuborildi: {user.email}")
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_subscription_confirmation(self, user_id):
    """Premium obuna tasdiqi emaili."""
    try:
        from accounts.models import User
        user = User.objects.get(id=user_id)
        send_mail(
            subject="Premium obuna faollashtirildi",
            message=f"Salom {user.first_name}, Premium obunangiz muvaffaqiyatli faollashtirildi!",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
        )
    except Exception as exc:
        raise self.retry(exc=exc)
