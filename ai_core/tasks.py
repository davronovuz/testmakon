"""
AI Core - Celery Tasks
Barcha og'ir AI operatsiyalar shu yerda background da ishlaydi.
"""
from celery import shared_task
import logging
import json

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def ai_chat_task(self, conversation_id):
    """
    Gemini API ni background da chaqirish.
    api_chat view tomonidan chaqiriladi.
    """
    try:
        from .models import AIConversation, AIMessage
        from .utils import get_ai_response

        conversation = AIConversation.objects.get(id=conversation_id)

        messages = list(conversation.messages.all().order_by('created_at'))
        history = [{"role": msg.role, "content": msg.content} for msg in messages]

        ai_response = get_ai_response(history)

        ai_msg = AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_response,
            model_used='gemini-1.5-flash'
        )

        new_title = None
        if conversation.title == 'Yangi suhbat':
            first_user = next((m for m in messages if m.role == 'user'), None)
            if first_user:
                conversation.title = first_user.content[:50]
                new_title = conversation.title

        conversation.message_count = conversation.messages.count()
        conversation.save(update_fields=['title', 'message_count', 'updated_at'])

        return {
            'response': ai_response,
            'conversation_uuid': str(conversation.uuid),
            'title': new_title,
        }

    except Exception as exc:
        logger.error(f"ai_chat_task xatolik: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def ai_analyze_test_task(self, attempt_id):
    """
    Test natijasini AI tahlili — background da ishlaydi.
    ai_analyze_test view tomonidan chaqiriladi.
    """
    try:
        from tests_app.models import TestAttempt, AttemptAnswer
        from .utils import get_ai_response

        attempt = TestAttempt.objects.get(id=attempt_id)

        answers = AttemptAnswer.objects.filter(attempt=attempt).select_related(
            'question', 'question__topic', 'question__subject'
        )

        topic_stats = {}
        for ans in answers:
            topic_name = ans.question.topic.name if ans.question.topic else "Umumiy"
            if topic_name not in topic_stats:
                topic_stats[topic_name] = {'correct': 0, 'total': 0}
            topic_stats[topic_name]['total'] += 1
            if ans.is_correct:
                topic_stats[topic_name]['correct'] += 1

        weak_topics = []
        strong_topics = []
        for topic, stats in topic_stats.items():
            pct = (stats['correct'] / stats['total']) * 100
            if pct < 60:
                weak_topics.append({'topic': topic, 'percentage': round(pct, 1)})
            elif pct >= 80:
                strong_topics.append({'topic': topic, 'percentage': round(pct, 1)})

        system_prompt = """Sen test natijalarini tahlil qiluvchi AI mentorisan.
        Abituriyentga qisqa, aniq va foydali tavsiyalar ber. O'zbek tilida javob ber."""

        analysis_prompt = f"""
        Test natijasi: {attempt.percentage}%
        To'g'ri javoblar: {attempt.correct_answers}/{attempt.total_questions}
        Mavzular: {json.dumps(topic_stats, ensure_ascii=False)}
        Sust mavzular: {[t['topic'] for t in weak_topics]}

        Qisqa tahlil va tavsiyalar ber.
        """

        messages_list = [{"role": "user", "content": analysis_prompt}]
        ai_analysis = get_ai_response(messages_list, system_prompt)

        attempt.ai_analysis = ai_analysis
        attempt.weak_topics = weak_topics
        attempt.strong_topics = strong_topics
        attempt.ai_recommendations = [f"{t['topic']} mavzusini takrorlang" for t in weak_topics[:3]]
        attempt.save(update_fields=['ai_analysis', 'weak_topics', 'strong_topics', 'ai_recommendations'])

        return {'status': 'done', 'attempt_uuid': str(attempt.uuid)}

    except Exception as exc:
        logger.error(f"ai_analyze_test_task xatolik: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def ai_explain_topic_task(self, conversation_id):
    """
    Mavzuni tushuntirish — background da ishlaydi.
    ai_explain_topic view tomonidan chaqiriladi.
    """
    try:
        from .models import AIConversation, AIMessage
        from .utils import get_ai_response

        conversation = AIConversation.objects.get(id=conversation_id)
        user_msg = conversation.messages.filter(role='user').last()
        if not user_msg:
            return

        system_prompt_text = conversation.system_prompt or """Sen professional o'qituvchisan.
        Mavzuni batafsil, misollar bilan tushuntir. O'zbek tilida javob ber."""

        messages_list = [{"role": "user", "content": user_msg.content}]
        explanation = get_ai_response(messages_list, system_prompt_text)

        AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=explanation,
            model_used='gemini-1.5-flash'
        )

        conversation.message_count = conversation.messages.count()
        conversation.save(update_fields=['message_count', 'updated_at'])

        return {'status': 'done', 'conversation_uuid': str(conversation.uuid)}

    except Exception as exc:
        logger.error(f"ai_explain_topic_task xatolik: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification_email(self, user_id, subject, message):
    """Email yuborish — background da ishlaydi."""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        from accounts.models import User

        user = User.objects.get(id=user_id)
        if not user.email:
            return

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f"Email yuborildi: {user.email}")

    except Exception as exc:
        logger.error(f"send_notification_email xatolik: {exc}")
        raise self.retry(exc=exc)
