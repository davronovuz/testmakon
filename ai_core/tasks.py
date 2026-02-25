from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_test_results(self, user_id, test_result_id):
    """
    Test natijalarini AI bilan tahlil qilish.
    Og'ir hisob-kitob — foydalanuvchini kutdirmaydi.
    """
    try:
        from accounts.models import User
        from tests_app.models import TestResult

        user = User.objects.get(id=user_id)
        result = TestResult.objects.get(id=test_result_id)

        # AI tahlil logikasi shu yerga
        logger.info(f"AI tahlil boshlandi: user={user_id}, result={test_result_id}")
        # ... google_generativeai chaqiruvi ...

    except Exception as exc:
        logger.error(f"analyze_test_results xatolik: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification_email(self, user_id, subject, message):
    """
    Email jo'natish — sinxron bo'lsa request ni sekinlashtiradi.
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        from accounts.models import User

        user = User.objects.get(id=user_id)
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Email yuborildi: {user.email}")

    except Exception as exc:
        logger.error(f"send_notification_email xatolik: {exc}")
        raise self.retry(exc=exc)


@shared_task
def generate_weekly_report(user_id):
    """
    Haftalik hisobot PDF — og'ir va vaqt oladigan jarayon.
    """
    try:
        logger.info(f"Haftalik hisobot tayyorlanmoqda: user={user_id}")
        # PDF generatsiya logikasi shu yerga
    except Exception as exc:
        logger.error(f"generate_weekly_report xatolik: {exc}")
