"""
TestMakon.uz - AI Core Views
AI Mentor, Analysis, Study Plans with Claude API integration
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_POST
import json
from datetime import timedelta, datetime
import google.generativeai as genai

from .models import (
    AIConversation, AIMessage, AIRecommendation,
    StudyPlan, StudyPlanTask, WeakTopicAnalysis
)
from tests_app.models import Subject, Topic, TestAttempt, AttemptAnswer, Test
from universities.models import University, Direction, PassingScore


def generate_plan_tasks(plan):
    """Reja yaratilganda haftalik vazifalarni avtomatik yaratish (4 hafta yoki imtihon sanasigacha)."""
    from datetime import date
    subjects = list(plan.subjects.all())
    if not subjects:
        return
    today = timezone.localdate()
    # target_exam_date ni to'g'ri tekshirish - date obyekti bo'lishi kerak
    if plan.target_exam_date and isinstance(plan.target_exam_date, date):
        if plan.target_exam_date > today:
            end_date = plan.target_exam_date
        else:
            end_date = today + timedelta(days=28)
    else:
        end_date = today + timedelta(days=28)
    days_count = max(1, (end_date - today).days)
    weekly_days = max(1, min(7, plan.weekly_days))
    daily_hours = max(0.5, plan.daily_hours)
    subject_index = 0
    order = 0
    for day_offset in range(days_count):
        current_date = today + timedelta(days=day_offset)
        if current_date > end_date:
            break
        weekday = current_date.weekday()
        if weekday >= weekly_days:
            continue
        subject = subjects[subject_index % len(subjects)]
        subject_index += 1
        title = f"{subject.name} — mashq"
        StudyPlanTask.objects.create(
            study_plan=plan,
            title=title,
            task_type='practice',
            subject=subject,
            scheduled_date=current_date,
            estimated_minutes=min(60, int(daily_hours * 60 / 2)),
            questions_count=10,
            order=order
        )
        order += 1
    plan.total_tasks = plan.tasks.count()
    plan.save(update_fields=['total_tasks'])


def get_ai_response(messages_list, system_prompt=None):
    """Gemini API bilan bog'lanish"""
    api_key = settings.GEMINI_API_KEY

    if not api_key:
        return "AI xizmati hozircha mavjud emas. Iltimos, keyinroq urinib ko'ring."

    try:
        genai.configure(api_key=api_key)

        # System promptni sozlash
        if system_prompt is None:
            system_prompt = """Sen TestMakon.uz platformasining AI mentorisan. 
            Sening vazifang O'zbekistondagi abituriyentlarga universitetga kirish imtihonlariga tayyorlanishda yordam berish.
            Sen o'zbek tilida javob berasan. Javoblaringni qisqa, aniq va foydali qilib ber."""

        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_prompt)

        # Tarixni formatlash (Gemini uchun)
        chat_history = []
        last_user_message = ""

        for msg in messages_list:
            role = "user" if msg['role'] == "user" else "model"
            content = msg['content']

            if role == "user":
                last_user_message = content

            # Oxirgi xabarni chat_history ga qo'shmaymiz, uni alohida yuboramiz
            if msg != messages_list[-1]:
                chat_history.append({"role": role, "parts": [content]})

        chat = model.start_chat(history=chat_history)
        response = chat.send_message(last_user_message)

        return response.text

    except Exception as e:
        return f"Texnik xatolik: {str(e)}"


@login_required
def ai_mentor(request):
    """AI Mentor bosh sahifasi"""
    conversations = AIConversation.objects.filter(
        user=request.user
    ).order_by('-updated_at')[:5]

    subjects = Subject.objects.filter(is_active=True)

    context = {
        'conversations': conversations,
        'subjects': subjects,
    }

    return render(request, 'ai_core/ai_mentor.html', context)


@login_required
def ai_chat(request):
    """AI bilan chat - yangi suhbat"""
    conversation = AIConversation.objects.create(
        user=request.user,
        conversation_type='mentor',
        title='Yangi suhbat'
    )

    return redirect('ai_core:conversation_detail', uuid=conversation.uuid)


@login_required
def conversation_detail(request, uuid):
    """Suhbat sahifasi — faqat ko‘rsatish; xabar yuborish api_chat orqali (AJAX)."""
    conversation = get_object_or_404(
        AIConversation,
        uuid=uuid,
        user=request.user
    )
    messages_list = conversation.messages.all().order_by('created_at')

    context = {
        'conversation': conversation,
        'messages': messages_list,
    }
    return render(request, 'ai_core/conversation_detail.html', context)


@login_required
def conversations_list(request):
    """Barcha suhbatlar"""
    conversations = AIConversation.objects.filter(
        user=request.user
    ).order_by('-updated_at')

    context = {
        'conversations': conversations,
    }

    return render(request, 'ai_core/conversations_list.html', context)


@login_required
def ai_tutor(request):
    """AI mavzu tushuntiruvchi"""
    subjects = Subject.objects.filter(is_active=True).prefetch_related('topics')

    context = {
        'subjects': subjects,
    }

    return render(request, 'ai_core/ai_tutor.html', context)


@login_required
def ai_explain_topic(request):
    """Mavzuni tushuntirish"""
    if request.method == 'POST':
        topic_name = request.POST.get('topic', '')
        subject_id = request.POST.get('subject_id', '')
        detail_level = request.POST.get('detail_level', 'normal')

        subject = Subject.objects.filter(id=subject_id).first()
        subject_name = subject.name if subject else "Umumiy"

        system_prompt = f"""Sen {subject_name} fani bo'yicha professional o'qituvchisan.
        Mavzuni {"juda sodda, bolalar tushunadigan tilda" if detail_level == "simple" else "batafsil, misollar bilan"} tushuntir.
        O'zbek tilida javob ber."""

        messages_list = [
            {"role": "user", "content": f"Menga '{topic_name}' mavzusini tushuntir."}
        ]

        explanation = get_ai_response(messages_list, system_prompt)

        conversation = AIConversation.objects.create(
            user=request.user,
            conversation_type='tutor',
            title=f"{subject_name}: {topic_name}",
            subject=subject
        )

        AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content=f"Menga '{topic_name}' mavzusini tushuntir."
        )

        AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=explanation
        )

        return redirect('ai_core:conversation_detail', uuid=conversation.uuid)

    return redirect('ai_core:ai_tutor')


@login_required
def ai_analyze_test(request, attempt_uuid):
    """Test natijasini AI tahlili"""
    attempt = get_object_or_404(
        TestAttempt,
        uuid=attempt_uuid,
        user=request.user,
        status='completed'
    )

    if attempt.ai_analysis:
        context = {
            'attempt': attempt,
            'analysis': attempt.ai_analysis,
            'recommendations': attempt.ai_recommendations,
            'weak_topics': attempt.weak_topics,
            'strong_topics': attempt.strong_topics,
        }
        return render(request, 'ai_core/test_analysis.html', context)

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
        percentage = (stats['correct'] / stats['total']) * 100
        if percentage < 60:
            weak_topics.append({'topic': topic, 'percentage': percentage})
        elif percentage >= 80:
            strong_topics.append({'topic': topic, 'percentage': percentage})

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
    attempt.save()

    context = {
        'attempt': attempt,
        'analysis': ai_analysis,
        'recommendations': attempt.ai_recommendations,
        'weak_topics': weak_topics,
        'strong_topics': strong_topics,
    }

    return render(request, 'ai_core/test_analysis.html', context)


@login_required
def ai_detailed_analysis(request, attempt_uuid):
    """Batafsil tahlil"""
    attempt = get_object_or_404(TestAttempt, uuid=attempt_uuid, user=request.user)
    answers = AttemptAnswer.objects.filter(attempt=attempt).select_related(
        'question', 'selected_answer', 'question__topic'
    )

    context = {
        'attempt': attempt,
        'answers': answers,
    }

    return render(request, 'ai_core/detailed_analysis.html', context)


@login_required
def ai_advisor(request):
    """AI universitet maslahatchisi"""
    subjects = Subject.objects.filter(is_active=True)

    from django.db.models import Avg
    user_stats = {}
    for subject in subjects:
        avg = TestAttempt.objects.filter(
            user=request.user,
            test__subject=subject,
            status='completed'
        ).aggregate(Avg('percentage'))['percentage__avg']

        if avg:
            user_stats[subject.id] = round(avg, 1)

    context = {
        'subjects': subjects,
        'user_stats': user_stats,
    }

    return render(request, 'ai_core/ai_advisor.html', context)


@login_required
def ai_calculate_admission(request):
    """Qabul kalkulyatori"""
    if request.method == 'POST':
        total_score = float(request.POST.get('total_score', 0))

        current_year = timezone.now().year
        recommendations = []

        directions = Direction.objects.filter(is_active=True).select_related('university')

        for direction in directions:
            last_score = PassingScore.objects.filter(
                direction=direction,
                year=current_year - 1
            ).first()

            if last_score:
                grant_chance = 0
                contract_chance = 0

                if last_score.grant_score:
                    if total_score >= last_score.grant_score:
                        grant_chance = 90
                    elif total_score >= last_score.grant_score - 10:
                        grant_chance = 60
                    elif total_score >= last_score.grant_score - 20:
                        grant_chance = 30

                if last_score.contract_score:
                    if total_score >= last_score.contract_score:
                        contract_chance = 95
                    elif total_score >= last_score.contract_score - 10:
                        contract_chance = 70
                    elif total_score >= last_score.contract_score - 20:
                        contract_chance = 40

                if grant_chance > 0 or contract_chance > 0:
                    recommendations.append({
                        'direction': direction,
                        'university': direction.university,
                        'grant_chance': grant_chance,
                        'contract_chance': contract_chance,
                        'last_grant_score': last_score.grant_score,
                        'last_contract_score': last_score.contract_score,
                    })

        recommendations.sort(key=lambda x: x['grant_chance'], reverse=True)

        context = {
            'total_score': total_score,
            'recommendations': recommendations[:20],
        }

        return render(request, 'ai_core/admission_results.html', context)

    return redirect('ai_core:ai_advisor')


@login_required
def study_plan_list(request):
    """O'quv rejalar ro'yxati"""
    plans = StudyPlan.objects.filter(user=request.user).order_by('-created_at')

    context = {'plans': plans}
    return render(request, 'ai_core/study_plan_list.html', context)


@login_required
def study_plan_create(request):
    """Yangi o'quv reja — kerakli ma'lumotlarni so'rab, vazifalarni avtomatik yaratadi."""
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip() or "O'quv reja"
        target_date_str = request.POST.get('target_date', '').strip()
        target_score = request.POST.get('target_score')
        subject_ids = request.POST.getlist('subjects')
        daily_hours = float(request.POST.get('daily_hours', 2))
        weekly_days = int(request.POST.get('weekly_days', 6))

        target_exam_date = None
        if target_date_str:
            try:
                target_exam_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                target_exam_date = None

        plan = StudyPlan.objects.create(
            user=request.user,
            title=title,
            target_exam_date=target_exam_date,
            target_score=int(target_score) if target_score else None,
            daily_hours=daily_hours,
            weekly_days=min(7, max(1, weekly_days))
        )

        if subject_ids:
            plan.subjects.set(subject_ids)
            generate_plan_tasks(plan)

        messages.success(request, "O'quv reja yaratildi! Haftalik vazifalar tayyor.")
        return redirect('ai_core:study_plan_detail', uuid=plan.uuid)

    subjects = Subject.objects.filter(is_active=True).order_by('order', 'name')
    context = {'subjects': subjects}
    return render(request, 'ai_core/study_plan_create.html', context)


@login_required
def study_plan_detail(request, uuid):
    """O'quv reja — countdown, haftalik taqvim, vazifalar kartochkalari."""
    plan = get_object_or_404(StudyPlan, uuid=uuid, user=request.user)

    today = timezone.localdate()
    week_start_str = request.GET.get('week')
    if week_start_str:
        try:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        except ValueError:
            week_start = today - timedelta(days=(today.weekday() + 1) % 7)
    else:
        week_start = today - timedelta(days=(today.weekday() + 1) % 7)

    week_days = []
    day_names = ['Yak', 'Dush', 'Sesh', 'Chor', 'Pay', 'Jum', 'Shan']
    for i in range(7):
        d = week_start + timedelta(days=i)
        day_tasks = plan.tasks.filter(scheduled_date=d).order_by('order')
        week_days.append({
            'date': d,
            'day_name': day_names[i],
            'is_today': d == today,
            'tasks': day_tasks,
        })

    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)
    current_week_start = today - timedelta(days=(today.weekday() + 1) % 7)
    days_left = None
    if plan.target_exam_date and plan.target_exam_date >= today:
        days_left = (plan.target_exam_date - today).days

    context = {
        'plan': plan,
        'week_start': week_start,
        'week_days': week_days,
        'prev_week': prev_week,
        'next_week': next_week,
        'current_week_start': current_week_start,
        'today': today,
        'days_left': days_left,
    }
    return render(request, 'ai_core/study_plan_detail.html', context)


@login_required
def study_plan_update(request, uuid):
    """Reja holati (faol/to'xtatilgan) yangilash."""
    plan = get_object_or_404(StudyPlan, uuid=uuid, user=request.user)
    if request.method == 'POST':
        plan.status = request.POST.get('status', plan.status)
        plan.save()
        messages.success(request, "Reja yangilandi")
    return redirect('ai_core:study_plan_detail', uuid=uuid)


@login_required
def study_plan_edit(request, uuid):
    """Rejani tahrirlash — imtihon sanasi, fanlar, vaqt."""
    plan = get_object_or_404(StudyPlan, uuid=uuid, user=request.user)
    if request.method == 'POST':
        plan.title = (request.POST.get('title') or '').strip() or plan.title
        td = request.POST.get('target_date')
        if td:
            plan.target_exam_date = datetime.strptime(td, '%Y-%m-%d').date()
        else:
            plan.target_exam_date = None
        plan.target_score = int(request.POST.get('target_score')) if request.POST.get('target_score') else None
        plan.daily_hours = float(request.POST.get('daily_hours', plan.daily_hours))
        plan.weekly_days = min(7, max(1, int(request.POST.get('weekly_days', plan.weekly_days))))
        plan.save()
        subject_ids = request.POST.getlist('subjects')
        if subject_ids is not None:
            plan.subjects.set(subject_ids)
        messages.success(request, "Reja saqlandi.")
        return redirect('ai_core:study_plan_detail', uuid=uuid)
    subjects = Subject.objects.filter(is_active=True).order_by('order', 'name')
    context = {'plan': plan, 'subjects': subjects}
    return render(request, 'ai_core/study_plan_edit.html', context)


@login_required
def study_plan_delete(request, uuid):
    """Rejani o'chirish."""
    plan = get_object_or_404(StudyPlan, uuid=uuid, user=request.user)
    if request.method == 'POST':
        plan.delete()
        messages.success(request, "Reja o'chirildi.")
        return redirect('ai_core:study_plan_list')
    return redirect('ai_core:study_plan_detail', uuid=uuid)


@login_required
def task_complete(request, task_id):
    """Vazifani bajarish"""
    task = get_object_or_404(StudyPlanTask, id=task_id, study_plan__user=request.user)

    task.is_completed = True
    task.completed_at = timezone.now()
    task.save()

    plan = task.study_plan
    plan.completed_tasks += 1
    plan.update_progress()

    messages.success(request, "Vazifa bajarildi! ✅")
    return redirect('ai_core:study_plan_detail', uuid=plan.uuid)


@login_required
def recommendations_list(request):
    """AI tavsiyalar ro'yxati"""
    recommendations = AIRecommendation.objects.filter(
        user=request.user,
        is_dismissed=False
    ).order_by('-priority', '-created_at')

    context = {'recommendations': recommendations}
    return render(request, 'ai_core/recommendations_list.html', context)


@login_required
def recommendation_dismiss(request, id):
    """Tavsiyani yopish"""
    rec = get_object_or_404(AIRecommendation, id=id, user=request.user)
    rec.is_dismissed = True
    rec.save()

    return redirect('ai_core:recommendations_list')


@login_required
def weak_topics(request):
    """Sust mavzular"""
    weak = WeakTopicAnalysis.objects.filter(
        user=request.user
    ).select_related('subject', 'topic').order_by('accuracy_rate')

    context = {'weak_topics': weak}
    return render(request, 'ai_core/weak_topics.html', context)


# API Views

@login_required
@require_POST
def api_chat(request):
    """Chat API — xabar yuborish va AI javob olish (AJAX uchun)."""
    try:
        data = json.loads(request.body)
        message = (data.get('message') or '').strip()
        conversation_uuid = data.get('conversation_uuid')

        if not message:
            return JsonResponse({'error': 'Xabar bo\'sh'}, status=400)

        if conversation_uuid:
            conversation = get_object_or_404(
                AIConversation, uuid=conversation_uuid, user=request.user
            )
        else:
            conversation = AIConversation.objects.create(
                user=request.user,
                conversation_type='mentor',
                title=message[:50] or 'Yangi suhbat'
            )

        AIMessage.objects.create(conversation=conversation, role='user', content=message)

        history = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation.messages.all().order_by('created_at')
        ]
        ai_response = get_ai_response(history)

        AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_response,
            model_used='gemini-1.5-flash'
        )

        new_title = None
        if conversation.title == 'Yangi suhbat':
            conversation.title = message[:50] or 'Yangi suhbat'
            new_title = conversation.title
        conversation.message_count = conversation.messages.count()
        conversation.save()

        return JsonResponse({
            'response': ai_response,
            'conversation_uuid': str(conversation.uuid),
            'title': new_title,
        })
    except json.JSONDecodeError as e:
        return JsonResponse({'error': 'Noto‘g‘ri so‘rov'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def api_quick_answer(request):
    """Tezkor javob API"""
    try:
        data = json.loads(request.body)
        question = data.get('question', '')
        subject = data.get('subject', '')

        if not question:
            return JsonResponse({'error': 'Savol bo\'sh'}, status=400)

        system_prompt = f"""Sen {subject if subject else 'umumiy'} fani bo'yicha ekspertsan.
        Savolga qisqa va aniq javob ber. O'zbek tilida javob ber."""

        messages_list = [{"role": "user", "content": question}]
        answer = get_ai_response(messages_list, system_prompt)

        return JsonResponse({'answer': answer})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def api_analyze(request):
    """Tahlil API"""
    try:
        data = json.loads(request.body)
        attempt_uuid = data.get('attempt_uuid')

        attempt = get_object_or_404(TestAttempt, uuid=attempt_uuid, user=request.user)

        analysis_data = {
            'percentage': attempt.percentage,
            'correct': attempt.correct_answers,
            'total': attempt.total_questions,
            'weak_topics': attempt.weak_topics,
            'strong_topics': attempt.strong_topics,
            'ai_analysis': attempt.ai_analysis,
        }

        return JsonResponse(analysis_data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)