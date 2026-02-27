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


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def generate_ai_study_plan_task(self, plan_id):
    """
    AI foydalanuvchi ma'lumotlariga qarab reja vazifalarini tuzadi.
    study_plan_create view tomonidan chaqiriladi.
    """
    try:
        from .models import StudyPlan, StudyPlanTask
        from .utils import get_ai_response
        from tests_app.models import TestAttempt
        from ai_core.models import WeakTopicAnalysis

        plan = StudyPlan.objects.get(id=plan_id)
        user = plan.user
        subjects = list(plan.subjects.all())
        today = timezone.localdate()

        # 1. Fan bo'yicha natijalar
        subject_stats = {}
        for attempt in TestAttempt.objects.filter(
            user=user, status='completed'
        ).select_related('test__subject').order_by('-completed_at')[:30]:
            subj = attempt.test.subject if attempt.test else None
            if subj:
                key = subj.name
                if key not in subject_stats:
                    subject_stats[key] = {'scores': []}
                subject_stats[key]['scores'].append(attempt.percentage)

        for key, val in subject_stats.items():
            scores = val['scores']
            val['avg'] = round(sum(scores) / len(scores), 1)
            val['count'] = len(scores)
            del val['scores']

        # 2. Sust mavzular
        weak_data = [
            {'subject': wt.subject.name, 'topic': wt.topic.name, 'accuracy': round(wt.accuracy_rate, 1)}
            for wt in WeakTopicAnalysis.objects.filter(
                user=user, subject__in=subjects
            ).select_related('subject', 'topic').order_by('accuracy_rate')[:12]
        ]

        # 3. Kunlar soni (max 28 kun — katta prompt AI ni sekinlashtiradi)
        if plan.target_exam_date and plan.target_exam_date > today:
            days_count = min(28, (plan.target_exam_date - today).days)
        else:
            days_count = 28

        subject_names = [s.name for s in subjects]
        system_prompt = (
            "Sen TestMakon.uz ning AI o'quv reja tuzuvchisan. "
            "Foydalanuvchi ma'lumotlariga qarab maqsadli kunlik vazifalar rej tuz. "
            "Javobni FAQAT sof JSON formatida ber, boshqa hech narsa yozma."
        )
        user_prompt = f"""Foydalanuvchi:
- Fanlar: {subject_names}
- Kun soni: {days_count} kun
- Kunlik: {plan.daily_hours} soat, haftada {plan.weekly_days} kun
- Maqsad: {plan.target_score or 'belgilanmagan'} ball

Test natijalari: {json.dumps(subject_stats, ensure_ascii=False)}
Sust mavzular: {json.dumps(weak_data, ensure_ascii=False)}

Quyidagi JSON formatda javob ber:
{{
  "analysis": "Foydalanuvchi haqida 2-3 gaplik tahlil",
  "tasks": [
    {{
      "day_offset": 0,
      "title": "Vazifa sarlavhasi",
      "subject": "Fan nomi",
      "topic": "Mavzu yoki null",
      "task_type": "study|practice|review|test",
      "difficulty": "easy|medium|hard",
      "minutes": 45,
      "notes": "Nega bu vazifa muhim (1 gap)",
      "is_weak_topic": true
    }}
  ]
}}"""

        response = get_ai_response([{"role": "user", "content": user_prompt}], system_prompt)

        # JSON ajratish
        match = re.search(r'\{[\s\S]*\}', response)
        if not match:
            raise ValueError("AI JSON javob bermadi")

        data = json.loads(match.group())

        # Subject/topic map
        subject_map = {s.name.lower(): s for s in subjects}
        topic_map = {}
        for s in subjects:
            for t in s.topics.all():
                topic_map[t.name.lower()] = t

        tasks_created = 0
        for item in data.get('tasks', []):
            day_offset = int(item.get('day_offset', 0))
            # weekly_days ga qarab skip
            scheduled = today + timedelta(days=day_offset)
            if scheduled.weekday() >= plan.weekly_days:
                continue

            subj_name = (item.get('subject') or '').lower()
            subj_obj = subject_map.get(subj_name)
            if not subj_obj:
                for k, v in subject_map.items():
                    if k in subj_name or subj_name in k:
                        subj_obj = v
                        break

            topic_name = (item.get('topic') or '').lower()
            topic_obj = topic_map.get(topic_name) if topic_name else None

            StudyPlanTask.objects.create(
                study_plan=plan,
                title=item.get('title', "O'quv vazifasi"),
                task_type=item.get('task_type', 'practice'),
                subject=subj_obj,
                topic=topic_obj,
                scheduled_date=scheduled,
                estimated_minutes=int(item.get('minutes', 30)),
                questions_count=10 if item.get('task_type') in ['test', 'practice'] else None,
                ai_notes=item.get('notes', ''),
                difficulty=item.get('difficulty', 'medium'),
                weak_topic_focus=bool(item.get('is_weak_topic', False)),
                order=tasks_created,
            )
            tasks_created += 1

        plan.total_tasks = tasks_created
        plan.is_ai_generated = True
        plan.ai_analysis = data.get('analysis', '')
        plan.save(update_fields=['total_tasks', 'is_ai_generated', 'ai_analysis'])

        # Agar AI 0 ta vazifa yaratsa — oddiy fallback reja tuz
        if tasks_created == 0:
            logger.warning(f"AI 0 vazifa yaratdi, fallback ishlatilmoqda: plan={plan_id}")
            _create_basic_tasks(plan, subjects, today, days_count)

        logger.info(f"AI reja tuzildi: plan={plan_id}, {tasks_created} vazifa")
        return {'status': 'done', 'tasks_created': plan.total_tasks}

    except Exception as exc:
        logger.error(f"generate_ai_study_plan_task xatolik: {exc}")
        # Retry o'rniga fallback — plan bo'sh qolmasin
        try:
            from .models import StudyPlan
            plan = StudyPlan.objects.get(id=plan_id)
            if plan.total_tasks == 0:
                subjects = list(plan.subjects.all())
                today = timezone.localdate()
                if plan.target_exam_date and plan.target_exam_date > today:
                    days_count = min(28, (plan.target_exam_date - today).days)
                else:
                    days_count = 28
                _create_basic_tasks(plan, subjects, today, days_count)
                logger.info(f"Fallback reja tuzildi: plan={plan_id}")
        except Exception as fb_exc:
            logger.error(f"Fallback xatolik: {fb_exc}")
        raise self.retry(exc=exc)


def _create_basic_tasks(plan, subjects, today, days_count):
    """AI ishlamasa oddiy haftalik vazifalar yaratadi."""
    from .models import StudyPlanTask
    if not subjects:
        return
    task_types = ['study', 'practice', 'review', 'test', 'practice', 'study']
    subj_idx = 0
    order = 0
    weekly_days = max(1, min(7, plan.weekly_days))
    for day_offset in range(days_count):
        current_date = today + timedelta(days=day_offset)
        if current_date.weekday() >= weekly_days:
            continue
        subject = subjects[subj_idx % len(subjects)]
        task_type = task_types[subj_idx % len(task_types)]
        subj_idx += 1
        StudyPlanTask.objects.create(
            study_plan=plan,
            title=f"{subject.name} — {task_type}",
            task_type=task_type,
            subject=subject,
            scheduled_date=current_date,
            estimated_minutes=int(plan.daily_hours * 60 // 2),
            questions_count=10 if task_type in ('test', 'practice') else None,
            difficulty='medium',
            order=order,
        )
        order += 1
    plan.total_tasks = plan.tasks.count()
    plan.save(update_fields=['total_tasks'])


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
