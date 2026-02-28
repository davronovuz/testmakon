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
from django.urls import reverse
import json
from datetime import timedelta, datetime

from .models import (
    AIConversation, AIMessage, AIRecommendation,
    StudyPlan, StudyPlanTask, WeakTopicAnalysis
)
from .utils import get_ai_response
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
        title = f"{subject.name} -- mashq"
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



@login_required
def ai_mentor(request):
    """AI Mentor bosh sahifasi"""
    conversations = AIConversation.objects.filter(
        user=request.user
    ).order_by('-updated_at')[:5]

    subjects = Subject.objects.filter(is_active=True)

    # AI tavsiyalar (oxirgi 5 ta, o'qilmagan)
    recommendations = AIRecommendation.objects.filter(
        user=request.user,
        is_dismissed=False,
    ).order_by('-created_at')[:6]

    # Sust mavzular (yuqori prioritet)
    weak_topics = WeakTopicAnalysis.objects.filter(
        user=request.user
    ).select_related('subject', 'topic').order_by('accuracy_rate')[:5]

    # Analytics summary
    try:
        analytics = request.user.analytics_summary
    except Exception:
        analytics = None

    context = {
        'conversations': conversations,
        'subjects': subjects,
        'recommendations': recommendations,
        'weak_topics': weak_topics,
        'analytics': analytics,
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
    """Suhbat sahifasi -- faqat ko'rsatish; xabar yuborish api_chat orqali (AJAX)."""
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

        conversation = AIConversation.objects.create(
            user=request.user,
            conversation_type='tutor',
            title=f"{subject_name}: {topic_name}",
            subject=subject,
            system_prompt=system_prompt
        )

        AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content=f"Menga '{topic_name}' mavzusini tushuntir."
        )

        # Celery task orqali tushuntirish olamiz
        from .tasks import ai_explain_topic_task
        ai_explain_topic_task.delay(conversation.id)

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

    # Tahlil yo'q -- Celery task ishga tushiramiz
    from .tasks import ai_analyze_test_task
    task = ai_analyze_test_task.delay(attempt.id)

    context = {
        'attempt': attempt,
        'analysis': None,
        'task_id': task.id,
        'recommendations': [],
        'weak_topics': [],
        'strong_topics': [],
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
    user_stats = []
    for subject in subjects:
        avg = TestAttempt.objects.filter(
            user=request.user,
            test__subject=subject,
            status='completed'
        ).aggregate(Avg('percentage'))['percentage__avg']

        if avg:
            user_stats.append({'name': subject.name, 'icon': subject.icon, 'score': round(avg, 1)})

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
    """Yangi o'quv reja -- AI yoki oddiy rejim."""
    if request.method == 'POST':
        mode = request.POST.get('mode', 'manual')
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

        if mode == 'ai':
            from .tasks import generate_ai_study_plan_task
            task = generate_ai_study_plan_task.delay(plan.id)
            detail_url = reverse('ai_core:study_plan_detail', kwargs={'uuid': plan.uuid})
            return redirect(f'{detail_url}?generating={task.id}')
        else:
            if subject_ids:
                generate_plan_tasks(plan)
            messages.success(request, "O'quv reja yaratildi! Haftalik vazifalar tayyor.")
            return redirect('ai_core:study_plan_detail', uuid=plan.uuid)

    subjects = Subject.objects.filter(is_active=True).order_by('order', 'name')
    context = {'subjects': subjects}
    return render(request, 'ai_core/study_plan_create.html', context)


@login_required
def study_plan_detail(request, uuid):
    """O'quv reja -- countdown, haftalik taqvim, vazifalar kartochkalari."""
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
        'generating_task_id': request.GET.get('generating'),
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
    """Rejani tahrirlash -- imtihon sanasi, fanlar, vaqt."""
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
@require_POST
def regenerate_ai_plan(request, uuid):
    """Rejani AI bilan qayta tuzish (eski vazifalarni o'chirib, yangisini yaratish)."""
    plan = get_object_or_404(StudyPlan, uuid=uuid, user=request.user)
    plan.tasks.all().delete()
    plan.total_tasks = 0
    plan.completed_tasks = 0
    plan.is_ai_generated = False
    plan.ai_analysis = ''
    plan.save(update_fields=['total_tasks', 'completed_tasks', 'is_ai_generated', 'ai_analysis'])
    from .tasks import generate_ai_study_plan_task
    task = generate_ai_study_plan_task.delay(plan.id)
    detail_url = reverse('ai_core:study_plan_detail', kwargs={'uuid': plan.uuid})
    return redirect(f'{detail_url}?generating={task.id}')


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
@require_POST
def start_task_test(request, task_id):
    """Smart test yaratishni background da ishga tushiradi."""
    task = get_object_or_404(StudyPlanTask, id=task_id, study_plan__user=request.user)
    if not task.subject:
        return JsonResponse({'error': 'Fan topilmadi'}, status=400)
    from .tasks import create_task_smart_test
    celery_task = create_task_smart_test.delay(task.id, request.user.id)
    return JsonResponse({'task_id': celery_task.id, 'status': 'pending'})


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
@require_POST
def conversation_delete(request, uuid):
    """Suhbatni o'chirish (AJAX POST)"""
    conversation = get_object_or_404(AIConversation, uuid=uuid, user=request.user)
    conversation.delete()
    return JsonResponse({'status': 'deleted'})


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
    """Chat API -- xabar saqlaydi, Celery task ishga tushiradi, task_id qaytaradi."""
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

        # Foydalanuvchi xabarini darhol saqlaymiz
        AIMessage.objects.create(conversation=conversation, role='user', content=message)

        # Celery task ishga tushiramiz -- AI javobini background da olamiz
        from .tasks import ai_chat_task
        task = ai_chat_task.delay(conversation.id)

        return JsonResponse({
            'task_id': task.id,
            'status': 'pending',
            'conversation_uuid': str(conversation.uuid),
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Noto\'g\'ri so\'rov'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def api_task_status(request, task_id):
    """Celery task holatini tekshirish — PROGRESS, done, error qaytaradi."""
    try:
        from celery.result import AsyncResult
        result = AsyncResult(task_id)

        if result.state == 'PROGRESS':
            meta = result.info or {}
            return JsonResponse({
                'status': 'pending',
                'current': meta.get('current', 0),
                'total': meta.get('total', 100),
                'step': meta.get('step', ''),
            })
        elif result.successful():
            data = result.get() or {}
            return JsonResponse({'status': 'done', **data})
        elif result.failed():
            return JsonResponse({'status': 'error'})
        else:
            return JsonResponse({
                'status': 'pending',
                'current': 0,
                'total': 100,
                'step': 'Navbat kutilmoqda...',
            })
    except Exception:
        return JsonResponse({'status': 'pending', 'current': 0, 'total': 100, 'step': ''})


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
def university_dashboard(request):
    """Universitet qabul dashboardi — predicted DTM asosida 3 toifaga bo'lingan."""
    from tests_app.models import UserAnalyticsSummary
    from django.db.models import Max

    try:
        analytics = request.user.analytics_summary
        predicted_dtm = analytics.predicted_dtm_score
    except Exception:
        analytics = None
        predicted_dtm = 0

    current_year = timezone.now().year
    latest_year = PassingScore.objects.aggregate(y=Max('year'))['y'] or (current_year - 1)

    passing_scores = PassingScore.objects.filter(
        year=latest_year,
        grant_score__isnull=False,
    ).select_related('direction__university').order_by('direction__university__name')

    safe_unis = []
    borderline_unis = []
    reach_unis = []
    contract_unis = []

    for ps in passing_scores:
        grant = ps.grant_score or 0
        contract = ps.contract_score or 0
        gap = predicted_dtm - grant

        entry = {
            'university': ps.direction.university,
            'direction': ps.direction,
            'grant_score': grant,
            'contract_score': contract,
            'gap': gap,
        }

        if predicted_dtm >= grant + 10:
            safe_unis.append(entry)
        elif predicted_dtm >= grant - 15:
            borderline_unis.append(entry)
        elif predicted_dtm >= grant - 40:
            reach_unis.append(entry)

        if contract > 0 and predicted_dtm >= contract and predicted_dtm < grant:
            contract_unis.append(entry)

    # AI tavsiyalar
    recommendations = AIRecommendation.objects.filter(
        user=request.user,
        recommendation_type='university',
        is_dismissed=False,
    ).order_by('-created_at')[:3]

    context = {
        'analytics': analytics,
        'predicted_dtm': predicted_dtm,
        'safe_unis': safe_unis[:10],
        'borderline_unis': borderline_unis[:10],
        'reach_unis': reach_unis[:10],
        'contract_unis': contract_unis[:8],
        'recommendations': recommendations,
        'latest_year': latest_year,
    }
    return render(request, 'ai_core/university_dashboard.html', context)


@login_required
def progress_dashboard(request):
    """Real-time progress dashboard — chart, peer comparison, weak topics."""
    from tests_app.models import (
        UserAnalyticsSummary, UserSubjectPerformance, UserTopicPerformance
    )
    import json as json_mod

    try:
        analytics = request.user.analytics_summary
    except Exception:
        analytics = None

    subject_perfs = UserSubjectPerformance.objects.filter(
        user=request.user
    ).select_related('subject').order_by('-average_score')

    weak_topic_perfs = UserTopicPerformance.objects.filter(
        user=request.user, is_weak=True
    ).select_related('subject', 'topic').order_by('current_score')[:10]

    # Oxirgi 30 kun kunlik ma'lumotlar
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_attempts = TestAttempt.objects.filter(
        user=request.user,
        status='completed',
        created_at__gte=thirty_days_ago,
    ).order_by('created_at').values('created_at', 'percentage')

    # Haftalik agregatsiya (Chart.js uchun)
    weekly_data = {}
    for attempt in recent_attempts:
        week_key = attempt['created_at'].strftime('%d.%m')
        if week_key not in weekly_data:
            weekly_data[week_key] = {'scores': [], 'count': 0}
        weekly_data[week_key]['scores'].append(attempt['percentage'])
        weekly_data[week_key]['count'] += 1

    chart_labels = []
    chart_scores = []
    for date_key in sorted(weekly_data.keys()):
        scores = weekly_data[date_key]['scores']
        chart_labels.append(date_key)
        chart_scores.append(round(sum(scores) / len(scores), 1) if scores else 0)

    # Radar chart — fan bo'yicha aniqlik
    radar_labels = [sp.subject.name for sp in subject_perfs]
    radar_scores = [round(sp.average_score, 1) for sp in subject_perfs]

    # Peer comparison — bir xil education_level dagi rank
    from accounts.models import User
    from django.db.models import Subquery, OuterRef
    from tests_app.models import UserAnalyticsSummary as UAS
    peer_count = UAS.objects.filter(
        user__education_level=request.user.education_level,
        user__is_active=True,
    ).count()

    user_dtm = analytics.predicted_dtm_score if analytics else 0
    peer_rank = UAS.objects.filter(
        user__education_level=request.user.education_level,
        user__is_active=True,
        predicted_dtm_score__gt=user_dtm,
    ).count() + 1

    context = {
        'analytics': analytics,
        'subject_perfs': subject_perfs,
        'weak_topic_perfs': weak_topic_perfs,
        'chart_labels': json_mod.dumps(chart_labels),
        'chart_scores': json_mod.dumps(chart_scores),
        'radar_labels': json_mod.dumps(radar_labels),
        'radar_scores': json_mod.dumps(radar_scores),
        'peer_rank': peer_rank,
        'peer_total': peer_count,
    }
    return render(request, 'ai_core/progress_dashboard.html', context)


@login_required
def behavioral_insights(request):
    """Behavioral insights — o'qish vaqti, charchash, uslub."""
    from tests_app.models import UserAnalyticsSummary, DailyUserStats

    try:
        analytics = request.user.analytics_summary
    except Exception:
        analytics = None

    # Burnout risk hisoblash
    burnout_risk = 'low'
    burnout_score = 0
    if analytics:
        if analytics.avg_session_duration > 90:
            burnout_score += 2
        if analytics.avg_questions_per_day > 50:
            burnout_score += 2
        if analytics.current_streak > 21:
            burnout_score += 1
        if burnout_score >= 4:
            burnout_risk = 'high'
        elif burnout_score >= 2:
            burnout_risk = 'medium'

    # Oxirgi 30 kun kunlik faollik (heatmap uchun)
    thirty_days_ago = timezone.localdate() - timedelta(days=30)
    daily_stats = DailyUserStats.objects.filter(
        user=request.user,
        date__gte=thirty_days_ago,
    ).order_by('date').values('date', 'accuracy_rate', 'tests_taken', 'activity_hours')

    # Soatlik taqsimlash (24 soat)
    hourly_activity = [0] * 24
    for ds in daily_stats:
        hours = ds['activity_hours'] or {}
        for hour_str, count in hours.items():
            try:
                hourly_activity[int(hour_str)] += count
            except (ValueError, IndexError):
                pass

    # 7-kunlik heatmap
    week_activity = []
    from tests_app.models import DailyUserStats as DUS
    for i in range(6, -1, -1):
        d = timezone.localdate() - timedelta(days=i)
        ds = DUS.objects.filter(user=request.user, date=d).first()
        week_activity.append({
            'date': d.strftime('%d.%m'),
            'tests': ds.tests_taken if ds else 0,
            'accuracy': round(ds.accuracy_rate, 0) if ds else 0,
            'active': bool(ds and ds.tests_taken > 0),
        })

    # AI strategy tavsiyasi (agar oxirgi 7 kunda yo'q bo'lsa — yangi generate)
    recent_strategy = AIRecommendation.objects.filter(
        user=request.user,
        recommendation_type='strategy',
        created_at__gte=timezone.now() - timedelta(days=7),
        is_dismissed=False,
    ).order_by('-created_at').first()

    context = {
        'analytics': analytics,
        'burnout_risk': burnout_risk,
        'burnout_score': burnout_score,
        'hourly_activity': hourly_activity,
        'week_activity': week_activity,
        'recent_strategy': recent_strategy,
    }
    return render(request, 'ai_core/behavioral_insights.html', context)


@login_required
@require_POST
def smart_test_generate(request):
    """Sust mavzular asosida AI Smart Test yaratish."""
    from tests_app.models import (
        Question, Test, TestQuestion, TestAttempt, Subject
    )

    subject_id = request.POST.get('subject_id')
    subject = None
    if subject_id:
        subject = Subject.objects.filter(id=subject_id).first()

    # Sust mavzularni top 5 tanlash
    weak_qs_filter = WeakTopicAnalysis.objects.filter(user=request.user)
    if subject:
        weak_qs_filter = weak_qs_filter.filter(subject=subject)
    weak_topic_ids = list(
        weak_qs_filter.order_by('accuracy_rate').values_list('topic_id', flat=True)[:5]
    )

    # Savollarni tanlash
    if subject:
        q_filter = Question.objects.filter(subject=subject, is_active=True)
    else:
        q_filter = Question.objects.filter(is_active=True)

    if weak_topic_ids:
        weak_questions = list(q_filter.filter(topic_id__in=weak_topic_ids).order_by('?')[:15])
        other_questions = list(q_filter.exclude(topic_id__in=weak_topic_ids).order_by('?')[:5])
        questions = (weak_questions + other_questions)[:20]
    else:
        questions = list(q_filter.order_by('?')[:20])

    if not questions:
        messages.error(request, "Savollar topilmadi. Avval testlar ishlang.")
        return redirect('ai_core:weak_topics')

    subject_for_test = subject or (questions[0].subject if questions else None)
    test = Test.objects.create(
        title=f"AI Smart Test — {subject_for_test.name if subject_for_test else 'Aralash'}",
        slug=f"ai-smart-{request.user.id}-{int(timezone.now().timestamp())}",
        test_type='practice',
        subject=subject_for_test,
        time_limit=len(questions) * 2,
        question_count=len(questions),
        shuffle_questions=True,
        shuffle_answers=True,
        show_correct_answers=True,
        created_by=request.user,
    )
    for i, q in enumerate(questions):
        TestQuestion.objects.create(test=test, question=q, order=i)

    attempt = TestAttempt.objects.create(
        user=request.user,
        test=test,
        total_questions=len(questions),
        status='in_progress',
    )

    return redirect('tests_app:test_play', uuid=attempt.uuid)


@login_required
def smart_test_status(request, task_id):
    """Smart test Celery task holati (api_task_status bilan bir xil)."""
    return api_task_status(request, task_id)


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