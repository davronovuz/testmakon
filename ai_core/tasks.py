"""
AI Core - Celery Tasks
Barcha og'ir AI operatsiyalar shu yerda background da ishlaydi.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
import json
import re

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def ai_chat_task(self, conversation_id):
    """
    Gemini API ni background da chaqirish.
    api_chat view tomonidan chaqiriladi.
    User profili system_prompt ga inject qilinadi — shaxsiy AI mentor.
    """
    try:
        from .models import AIConversation, AIMessage
        from .utils import get_ai_response, get_user_ai_context

        conversation = AIConversation.objects.select_related('user').get(id=conversation_id)

        messages = list(conversation.messages.all().order_by('created_at'))
        history = [{"role": msg.role, "content": msg.content} for msg in messages]

        # Foydalanuvchi kontekstini system_prompt ga inject qilish
        if conversation.system_prompt:
            system_prompt = conversation.system_prompt
        else:
            system_prompt = get_user_ai_context(conversation.user)

        ai_response = get_ai_response(history, system_prompt=system_prompt)

        ai_msg = AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_response,
            model_used='gemini-2.5-flash'
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
            model_used='gemini-2.5-flash'
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


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_ai_study_plan_task(self, plan_id):
    """
    AI o'quv reja — Celery thin wrapper.
    Barcha biznes logika: ai_core/services.py → StudyPlanService.
    """
    def on_progress(percent, step):
        self.update_state(
            state='PROGRESS',
            meta={'current': percent, 'total': 100, 'step': step},
        )

    try:
        from .services import StudyPlanService
        on_progress(5, "Boshlanmoqda...")
        service = StudyPlanService(plan_id, progress_callback=on_progress)
        tasks_created = service.run()
        return {'status': 'done', 'tasks_created': tasks_created}

    except Exception as exc:
        logger.error(f"generate_ai_study_plan_task xatolik: plan={plan_id} — {exc}")
        raise self.retry(exc=exc)



@shared_task
def send_daily_study_reminders():
    """
    Har kuni 8:00 da ishga tushadi.
    Bugun vazifalari bor foydalanuvchilarga bildirishnoma yaratadi.
    """
    from .models import StudyPlan, StudyPlanTask
    from news.models import Notification

    today = timezone.localdate()

    # Bugungi tugallanmagan vazifalar
    tasks_today = StudyPlanTask.objects.filter(
        scheduled_date=today,
        is_completed=False,
        study_plan__status='active'
    ).select_related('study_plan__user', 'subject').values(
        'study_plan__user_id',
        'study_plan__user__first_name',
        'subject__name',
    )

    # User bo'yicha guruhlash
    user_tasks = {}
    for t in tasks_today:
        uid = t['study_plan__user_id']
        if uid not in user_tasks:
            user_tasks[uid] = {'name': t['study_plan__user__first_name'], 'count': 0, 'subjects': set()}
        user_tasks[uid]['count'] += 1
        if t['subject__name']:
            user_tasks[uid]['subjects'].add(t['subject__name'])

    created = 0
    for user_id, info in user_tasks.items():
        # Bugun allaqachon yuborilmagan bo'lsa
        already = Notification.objects.filter(
            user_id=user_id,
            notification_type='system',
            created_at__date=today,
            title__startswith='📚 Bugungi'
        ).exists()
        if already:
            continue

        subjects_str = ', '.join(list(info['subjects'])[:3])
        Notification.objects.create(
            user_id=user_id,
            notification_type='system',
            title=f"📚 Bugungi o'quv vazifalar",
            message=f"Bugun {info['count']} ta vazifangiz bor: {subjects_str}. Bajarishni unutmang!",
            link='/ai/study-plan/',
        )
        created += 1

    # Kechiktirилган vazifalar (kecha tugallanmagan)
    yesterday = today - timedelta(days=1)
    overdue = StudyPlanTask.objects.filter(
        scheduled_date=yesterday,
        is_completed=False,
        study_plan__status='active'
    ).select_related('study_plan__user').values('study_plan__user_id').distinct()

    for row in overdue:
        uid = row['study_plan__user_id']
        already = Notification.objects.filter(
            user_id=uid,
            notification_type='warning',
            created_at__date=today,
            title__startswith='⚠️'
        ).exists()
        if already:
            continue
        Notification.objects.create(
            user_id=uid,
            notification_type='warning',
            title="⚠️ Bajarilmagan vazifalar",
            message="Kecha bir necha vazifangiz bajarilmay qoldi. Bugun ulgurib oling!",
            link='/ai/study-plan/',
        )

    logger.info(f"Kunlik eslatmalar: {created} ta yuborildi")


@shared_task(bind=True, max_retries=2)
def create_task_smart_test(self, task_id, user_id):
    """
    Vazifaning fanidan foydalanuvchining sust mavzulariga qarab
    maxsus test yaratadi va attempt ID qaytaradi.
    """
    try:
        from .models import StudyPlanTask
        from tests_app.models import (
            Question, Test, TestQuestion, TestAttempt, Subject
        )
        from ai_core.models import WeakTopicAnalysis

        task = StudyPlanTask.objects.select_related('subject', 'topic').get(id=task_id)
        subject = task.subject
        if not subject:
            return {'error': 'Fan topilmadi'}

        # Sust mavzularni topish
        weak_topic_ids = list(
            WeakTopicAnalysis.objects.filter(
                user_id=user_id, subject=subject
            ).order_by('accuracy_rate').values_list('topic_id', flat=True)[:5]
        )

        # Savollarni tanlash: sust mavzulardan priority
        if weak_topic_ids:
            weak_qs = list(
                Question.objects.filter(
                    subject=subject, topic_id__in=weak_topic_ids, is_active=True
                ).order_by('?')[:15]
            )
            other_qs = list(
                Question.objects.filter(
                    subject=subject, is_active=True
                ).exclude(topic_id__in=weak_topic_ids).order_by('?')[:5]
            )
            questions = (weak_qs + other_qs)[:20]
        else:
            questions = list(
                Question.objects.filter(subject=subject, is_active=True).order_by('?')[:20]
            )

        if not questions:
            return {'error': 'Savollar topilmadi'}

        # Test yaratish
        test = Test.objects.create(
            title=f"AI Test — {subject.name} ({task.title})",
            slug=f"ai-task-{task_id}-{user_id}-{int(timezone.now().timestamp())}",
            test_type='practice',
            subject=subject,
            time_limit=len(questions) * 2,
            question_count=len(questions),
            shuffle_questions=True,
            shuffle_answers=True,
            show_correct_answers=True,
            created_by_id=user_id,
        )
        for i, q in enumerate(questions):
            TestQuestion.objects.create(test=test, question=q, order=i)

        attempt = TestAttempt.objects.create(
            user_id=user_id,
            test=test,
            total_questions=len(questions),
            status='in_progress',
        )

        from django.urls import reverse
        play_url = reverse('tests_app:test_play', kwargs={'uuid': attempt.uuid})
        logger.info(f"Smart test yaratildi: task={task_id}, {len(questions)} savol")
        return {'status': 'done', 'attempt_uuid': str(attempt.uuid), 'play_url': play_url}

    except Exception as exc:
        logger.error(f"create_task_smart_test xatolik: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_university_recommendation(self, user_id, attempt_id):
    """
    Qatlam 3+4: Smart AI Advisor + DTM → Universitet tavsiyasi.
    Test tugagandan keyin foydalanuvchi uchun:
    1. Sust mavzular bo'yicha aniq tavsiyalar
    2. DTM ball bashorati asosida mos universitetlar tavsiyasi
    3. Shaxsiy motivatsion xat
    Natijalar AIRecommendation modeliga saqlanadi.
    """
    try:
        from .models import AIRecommendation, WeakTopicAnalysis
        from .utils import get_ai_response
        from tests_app.models import TestAttempt, UserSubjectPerformance, UserAnalyticsSummary
        from universities.models import University, Direction, PassingScore
        from accounts.models import User

        user = User.objects.select_related('target_university', 'target_direction').get(id=user_id)
        attempt = TestAttempt.objects.select_related('test', 'test__subject').get(id=attempt_id)

        # --- User konteksti yig'ish ---
        try:
            summary = user.analytics_summary
            predicted_dtm = summary.predicted_dtm_score
            overall_accuracy = summary.overall_accuracy
        except Exception:
            predicted_dtm = 0
            overall_accuracy = attempt.percentage

        # Fan natijalari
        subject_perfs = list(
            UserSubjectPerformance.objects.filter(user=user).select_related('subject').order_by('average_score')
        )
        subject_data = [
            {'fan': sp.subject.name, 'ball': round(sp.average_score, 1), 'eng_yaxshi': round(sp.best_score, 1)}
            for sp in subject_perfs
        ]

        # Sust mavzular
        weak_topics = list(
            WeakTopicAnalysis.objects.filter(user=user).select_related('subject', 'topic').order_by('accuracy_rate')[:8]
        )
        weak_data = [
            {'fan': wt.subject.name, 'mavzu': wt.topic.name, 'aniqlik': round(wt.accuracy_rate, 1)}
            for wt in weak_topics
        ]

        # Maqsadli universitet
        target_uni_name = str(user.target_university) if user.target_university else "belgilanmagan"
        target_dir_name = str(user.target_direction) if user.target_direction else "belgilanmagan"

        # Mos universitetlar (predicted_dtm asosida)
        matched_universities = []
        if predicted_dtm > 0:
            try:
                passing_scores = PassingScore.objects.filter(
                    grant_score__lte=predicted_dtm + 30,
                    grant_score__gte=max(0, predicted_dtm - 60),
                ).select_related('direction__university').order_by('grant_score')[:10]

                for ps in passing_scores:
                    uni = ps.direction.university
                    score = ps.grant_score or 0
                    chance = "Yuqori" if predicted_dtm >= score else ("O'rta" if predicted_dtm >= score - 20 else "Past")
                    matched_universities.append({
                        'universitet': str(uni),
                        'yo_nalish': str(ps.direction),
                        'o_tish_bali': score,
                        'imkoniyat': chance,
                    })
            except Exception:
                pass

        # --- Gemini dan AI tahlil so'rash ---
        system_prompt = """Sen O'zbekistonda DTM (Davlat Test Markazi) imtihoniga tayyorlanuvchi abituriyentlarga
professional maslahat beruvchi AI advisorsan. Javoblarni O'zbek tilida ber.
Qisqa, aniq, ilhomlantiradigan va AMALIY tavsiyalar ber. Juda ko'p matn yozma."""

        user_prompt = f"""Foydalanuvchi: {user.get_full_name() or user.username}
So'nggi test natijalari: {attempt.percentage:.0f}% ({attempt.correct_answers}/{attempt.total_questions})
Umumiy aniqlik: {overall_accuracy:.0f}%
Bashorat DTM ball: {predicted_dtm}/189
Maqsad: {target_uni_name} — {target_dir_name}

Fan natijalari:
{json.dumps(subject_data, ensure_ascii=False, indent=2)}

Sust mavzular:
{json.dumps(weak_data, ensure_ascii=False, indent=2)}

Mos universitetlar (DTM ball asosida):
{json.dumps(matched_universities[:5], ensure_ascii=False, indent=2)}

Quyidagilarni ber:
1. **Holat tahlili** (2-3 gap): Hozirgi natijalar yaxshi/yomonmi?
2. **3 ta konkret vazifa**: Eng sust mavzular uchun bugun nima qilish kerak?
3. **Universitet tavsiyasi**: Bashorat ball asosida eng mos 2-3 ta universitet/yo'nalish
4. **Motivatsiya** (1-2 gap): Qisqa ilhomlantiradigan so'z

Javobni markdown formatda ber. Qisqa, o'tkir, amaliy bo'lsin."""

        ai_advice = get_ai_response(
            [{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt
        )

        # --- AIRecommendation saqlash ---
        # 1. Umumiy tavsiya
        AIRecommendation.objects.create(
            user=user,
            recommendation_type='strategy',
            priority='high',
            title=f"AI Tahlil: {attempt.percentage:.0f}% — {attempt.test.title if attempt.test else 'Test'} natijasi",
            content=ai_advice,
            subject=attempt.test.subject if attempt.test else None,
        )

        # 2. Har bir sust mavzu uchun alohida tavsiya (eskisini o'chirib yangisini yozish)
        for wt_obj in weak_topics[:3]:
            # Eski o'qilmagan topik tavsiyasini o'chirish
            AIRecommendation.objects.filter(
                user=user,
                topic=wt_obj.topic,
                recommendation_type='topic',
                is_dismissed=False,
            ).delete()
            # Yangi tavsiya yaratish
            AIRecommendation.objects.create(
                user=user,
                recommendation_type='topic',
                priority='high' if wt_obj.accuracy_rate < 40 else 'medium',
                title=f"{wt_obj.topic.name} — {wt_obj.accuracy_rate:.0f}% aniqlik",
                content=(
                    f"{wt_obj.topic.name} mavzusida {wt_obj.accuracy_rate:.0f}% aniqlik. "
                    f"Jami {wt_obj.total_questions} ta savoldan {wt_obj.correct_answers} tasi to'g'ri. "
                    f"Bu mavzuni ustuvor o'rganing va qayta mashq qiling."
                ),
                subject=wt_obj.subject,
                topic=wt_obj.topic,
            )

        # 3. Universitet tavsiyasi (agar mos universitetlar topilsa)
        if matched_universities:
            top_match = matched_universities[0]
            gap = abs(predicted_dtm - top_match['o_tish_bali'])
            gap_text = (
                f"Agar {gap:.0f} ball qo'shsangiz, maqsadingizga erisha olasiz!"
                if predicted_dtm < top_match['o_tish_bali']
                else f"Siz allaqachon o'tish baliga {gap:.0f} ball ustisiz!"
            )
            AIRecommendation.objects.create(
                user=user,
                recommendation_type='university',
                priority='medium',
                title=f"Siz uchun mos universitet: {top_match['universitet']}",
                content=(
                    f"DTM ball bashoratingiz {predicted_dtm} ball.\n"
                    f"{top_match['universitet']} — {top_match['yo_nalish']} yo'nalishi "
                    f"(o'tish bali: {top_match['o_tish_bali']:.0f}).\n"
                    f"Imkoniyat: {top_match['imkoniyat']}.\n"
                    f"{gap_text}"
                ),
                action_url='/universities/',
                action_text="Universitetlarni ko'rish",
            )

        logger.info(
            f"generate_university_recommendation OK: user={user_id}, "
            f"dtm={predicted_dtm}, matched={len(matched_universities)}"
        )
        return {'status': 'done', 'recommendations_created': len(weak_topics[:3]) + 2}

    except Exception as exc:
        logger.error(f"generate_university_recommendation xato: user_id={user_id}, {exc}")
        raise self.retry(exc=exc)


@shared_task
def send_smart_behavioral_notifications():
    """
    Har kuni 18:00 da ishga tushadi.
    - Bugun test ishlaganlarni yutuq bilan tabriklaydi
    - 3+ kun streak foydalanuvchilarga maxsus tashakkur
    - O'tgan haftaga nisbatan natijasi yaxshilanganlarga motivatsiya
    """
    from accounts.models import User
    from news.models import Notification
    from tests_app.models import TestAttempt
    import django.db.models as dj_models

    today = timezone.localdate()
    this_week_start = today - timedelta(days=7)
    last_week_start = today - timedelta(days=14)
    created = 0

    # Bugun test ishlaganlar
    todays_attempts = TestAttempt.objects.filter(
        status='completed',
        created_at__date=today,
    ).values('user_id', 'percentage')

    user_today_best = {}
    for row in todays_attempts:
        uid = row['user_id']
        if uid not in user_today_best or row['percentage'] > user_today_best[uid]:
            user_today_best[uid] = row['percentage']

    for user_id, best_pct in user_today_best.items():
        already = Notification.objects.filter(
            user_id=user_id,
            notification_type='achievement',
            created_at__date=today,
            title__startswith='🏆 Bugun ajoyib'
        ).exists()
        if already:
            continue
        try:
            user = User.objects.get(id=user_id)
            streak = user.current_streak or 1
            Notification.objects.create(
                user_id=user_id,
                notification_type='achievement',
                title="🏆 Bugun ajoyib natija!",
                message=(
                    f"Bugun {best_pct:.0f}% natija ko'rsatdingiz! "
                    f"Joriy streak: {streak} kun. "
                    f"Shunday davom eting — maqsadga yaqinlashyapsiz!"
                ),
                link='/ai/progress/',
            )
            created += 1
        except User.DoesNotExist:
            continue

    # 3+ kun streak foydalanuvchilar (bugun test ishlamaganlar)
    streak_users = User.objects.filter(
        current_streak__gte=3,
        last_activity_date=today,
    ).exclude(id__in=list(user_today_best.keys()))

    for user in streak_users:
        already = Notification.objects.filter(
            user_id=user.id,
            notification_type='system',
            created_at__date=today,
            title__startswith='🔥'
        ).exists()
        if already:
            continue
        Notification.objects.create(
            user_id=user.id,
            notification_type='system',
            title=f"🔥 {user.current_streak} kunlik streak!",
            message=(
                f"Siz {user.current_streak} kun ketma-ket o'qidingiz — bu zo'r! "
                f"DTM imtihoniga tayyorgarlikni shu tartibda davom ettiring."
            ),
            link='/ai/progress/',
        )
        created += 1

    # O'tgan haftaga nisbatan yaxshilanganlar
    for user in User.objects.filter(last_activity_date__gte=this_week_start):
        try:
            this_avg = TestAttempt.objects.filter(
                user=user, status='completed',
                created_at__date__gte=this_week_start,
            ).aggregate(avg=dj_models.Avg('percentage'))['avg'] or 0

            last_avg = TestAttempt.objects.filter(
                user=user, status='completed',
                created_at__date__gte=last_week_start,
                created_at__date__lt=this_week_start,
            ).aggregate(avg=dj_models.Avg('percentage'))['avg'] or 0

            if this_avg > last_avg + 5 and last_avg > 0:
                already = Notification.objects.filter(
                    user_id=user.id,
                    notification_type='system',
                    created_at__date=today,
                    title__startswith='📈'
                ).exists()
                if not already:
                    improvement = this_avg - last_avg
                    Notification.objects.create(
                        user_id=user.id,
                        notification_type='system',
                        title="📈 Natijangiz yaxshilandi!",
                        message=(
                            f"Bu hafta o'rtacha natijangiz {this_avg:.0f}% — "
                            f"o'tgan haftaga nisbatan +{improvement:.0f}% oshdi. "
                            f"Shu sur'atda davom etsangiz, DTMda yaxshi natija olasiz!"
                        ),
                        link='/ai/progress/',
                    )
                    created += 1
        except Exception:
            continue

    logger.info(f"Behavioral notifications: {created} ta yaratildi")


@shared_task
def send_inactivity_reminders():
    """
    Har kuni 10:00 da ishga tushadi.
    2+ kun faol bo'lmagan foydalanuvchilarga eslatma yuboradi.
    5+ kun bo'lmaganlarni telegram orqali ham ogohlantirib.
    """
    from accounts.models import User
    from news.models import Notification

    today = timezone.localdate()
    two_days_ago = today - timedelta(days=2)
    five_days_ago = today - timedelta(days=5)
    created = 0

    # 2-4 kun faol bo'lmaganlar
    inactive_2 = User.objects.filter(
        last_activity_date__lte=two_days_ago,
        last_activity_date__gt=five_days_ago,
        is_active=True,
    )
    for user in inactive_2:
        already = Notification.objects.filter(
            user_id=user.id,
            notification_type='reminder',
            created_at__date=today,
        ).exists()
        if already:
            continue
        days_inactive = (today - user.last_activity_date).days
        Notification.objects.create(
            user_id=user.id,
            notification_type='reminder',
            title="📚 Testlar sizi kutmoqda",
            message=(
                f"{days_inactive} kun test ishlamadingiz. "
                f"DTMga tayyorgarlik muntazam mashq talab qiladi. "
                f"Bugun qaytib keling!"
            ),
            link='/tests/',
        )
        created += 1

    # 5+ kun faol bo'lmaganlar — kuchli eslatma + telegram
    inactive_5 = User.objects.filter(
        last_activity_date__lte=five_days_ago,
        is_active=True,
    ).exclude(last_activity_date=None)

    for user in inactive_5:
        already = Notification.objects.filter(
            user_id=user.id,
            notification_type='reminder',
            created_at__date=today,
        ).exists()
        if already:
            continue
        days_inactive = (today - user.last_activity_date).days
        Notification.objects.create(
            user_id=user.id,
            notification_type='reminder',
            title="⚠️ Uzoq vaqt bo'lmadingiz!",
            message=(
                f"{days_inactive} kun davomida platformaga kirmadingiz. "
                f"DTM imtihoni yaqinlashmoqda — bugun eng muhim qadam qiling!"
            ),
            link='/tests/',
        )
        created += 1

        # Telegram xabar yuborish
        if user.telegram_id:
            try:
                import requests
                from django.conf import settings as dj_settings
                bot_token = dj_settings.TELEGRAM_BOT_TOKEN
                if bot_token:
                    name = user.first_name or user.username or "O'quvchi"
                    text = (
                        f"⚠️ Salom, {name}!\n\n"
                        f"{days_inactive} kun TestMakon.uzga kirmagansiz.\n"
                        f"DTMga tayyorgarlik to'xtamaydi — bugun testlar ishlab keling! 💪\n\n"
                        f"🌐 testmakon.uz"
                    )
                    requests.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={"chat_id": user.telegram_id, "text": text},
                        timeout=5,
                    )
            except Exception as tg_err:
                logger.warning(f"Telegram xabar xatosi: user={user.id}, {tg_err}")

    logger.info(f"Inactivity reminders: {created} ta yaratildi")


@shared_task
def generate_weekly_ai_report(user_id=None):
    """
    Har dushanba 09:00 da ishga tushadi (yoki user_id bilan yakka chaqiriladi).
    Haftalik o'quv hisobotini Gemini orqali yaratadi va Notification yuboradi.
    """
    from accounts.models import User
    from news.models import Notification
    from tests_app.models import TestAttempt
    from .models import AIRecommendation
    from .utils import get_ai_response
    import django.db.models as dj_models

    today = timezone.localdate()
    week_ago = today - timedelta(days=7)
    two_weeks_ago = today - timedelta(days=14)

    if user_id:
        users = User.objects.filter(id=user_id, is_active=True)
    else:
        users = User.objects.filter(
            last_activity_date__gte=week_ago,
            is_active=True,
        )

    created = 0
    for user in users:
        try:
            this_week = TestAttempt.objects.filter(
                user=user, status='completed',
                created_at__date__gte=week_ago,
            )
            tests_this_week = this_week.count()
            avg_this_week = this_week.aggregate(avg=dj_models.Avg('percentage'))['avg'] or 0

            if tests_this_week == 0:
                continue

            last_week = TestAttempt.objects.filter(
                user=user, status='completed',
                created_at__date__gte=two_weeks_ago,
                created_at__date__lt=week_ago,
            )
            avg_last_week = last_week.aggregate(avg=dj_models.Avg('percentage'))['avg'] or 0

            try:
                predicted_dtm = user.analytics_summary.predicted_dtm_score
                weak_count = user.analytics_summary.weak_topics_count
            except Exception:
                predicted_dtm = 0
                weak_count = 0

            trend = "yaxshilandi" if avg_this_week > avg_last_week else "pasaydi"
            diff = abs(avg_this_week - avg_last_week)

            prompt = f"""O'quvchi: {user.get_full_name() or user.username}
Bu hafta ishlagan testlar: {tests_this_week} ta
Bu hafta o'rtacha natija: {avg_this_week:.0f}%
O'tgan haftaga nisbatan: {trend} ({diff:.0f}%)
Bashorat DTM bali: {predicted_dtm}/189
Sust mavzular soni: {weak_count}

Ushbu o'quvchi uchun 2-3 gapdan iborat qisqa, ilhomlantiradigan haftalik xulosa yoz.
Natija yaxshi bo'lsa maqta, yomonlashgan bo'lsa rag'batlantir. O'zbek tilida."""

            ai_text = get_ai_response(
                [{"role": "user", "content": prompt}],
                system_prompt="Sen motivatsion AI mentorsan. Qisqa, issiq, ilhomlantiradigan xabarlar yoz. O'zbek tilida."
            )

            AIRecommendation.objects.create(
                user=user,
                recommendation_type='motivation',
                priority='medium',
                title=f"Haftalik hisobot — {today.strftime('%d.%m.%Y')}",
                content=ai_text,
            )

            already = Notification.objects.filter(
                user=user,
                notification_type='system',
                created_at__date=today,
                title__startswith='📊 Haftalik'
            ).exists()
            if not already:
                Notification.objects.create(
                    user=user,
                    notification_type='system',
                    title="📊 Haftalik hisobotingiz tayyor",
                    message=(
                        f"Bu hafta {tests_this_week} ta test ishlabsiz. "
                        f"O'rtacha: {avg_this_week:.0f}%. AI tahlilni ko'rish uchun bosing."
                    ),
                    link='/ai/mentor/',
                )
            created += 1

        except Exception as err:
            logger.error(f"generate_weekly_ai_report xato: user={user.id}, {err}")
            continue

    logger.info(f"Haftalik hisobotlar: {created} ta yaratildi")
    return {'created': created}
