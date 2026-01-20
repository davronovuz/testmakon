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
import requests

from .models import (
    AIConversation, AIMessage, AIRecommendation,
    StudyPlan, StudyPlanTask, WeakTopicAnalysis
)
from tests_app.models import Subject, Topic, TestAttempt, AttemptAnswer
from universities.models import University, Direction, PassingScore


def get_ai_response(messages_list, system_prompt=None):
    """Claude API bilan bog'lanish"""
    api_key = settings.ANTHROPIC_API_KEY

    if not api_key:
        return "AI xizmati hozircha mavjud emas. Iltimos, keyinroq urinib ko'ring."

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }

    if system_prompt is None:
        system_prompt = """Sen TestMakon.uz platformasining AI mentorisan. 
        Sening vazifang O'zbekistondagi abituriyentlarga universitetga kirish imtihonlariga tayyorlanishda yordam berish.
        Sen o'zbek tilida javob berasan. Javoblaringni qisqa, aniq va foydali qilib ber."""

    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": messages_list
    }

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result['content'][0]['text']
        else:
            return "Xatolik yuz berdi. Iltimos, qayta urinib ko'ring."
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
    """Suhbat tafsilotlari"""
    conversation = get_object_or_404(
        AIConversation,
        uuid=uuid,
        user=request.user
    )

    messages_list = conversation.messages.all().order_by('created_at')

    if request.method == 'POST':
        user_message = request.POST.get('message', '').strip()

        if user_message:
            AIMessage.objects.create(
                conversation=conversation,
                role='user',
                content=user_message
            )

            history = [
                {"role": msg.role, "content": msg.content}
                for msg in messages_list
            ]
            history.append({"role": "user", "content": user_message})

            ai_response = get_ai_response(history)

            AIMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=ai_response,
                model_used='claude-3-haiku'
            )

            if conversation.title == 'Yangi suhbat':
                conversation.title = user_message[:50]

            conversation.message_count += 2
            conversation.save()

            return redirect('ai_core:conversation_detail', uuid=uuid)

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
    """Yangi o'quv reja yaratish"""
    if request.method == 'POST':
        title = request.POST.get('title')
        target_date = request.POST.get('target_date')
        target_score = request.POST.get('target_score')
        subject_ids = request.POST.getlist('subjects')
        daily_hours = float(request.POST.get('daily_hours', 2))

        plan = StudyPlan.objects.create(
            user=request.user,
            title=title,
            target_exam_date=target_date or None,
            target_score=int(target_score) if target_score else None,
            daily_hours=daily_hours
        )

        if subject_ids:
            plan.subjects.set(subject_ids)

        messages.success(request, "O'quv reja yaratildi!")
        return redirect('ai_core:study_plan_detail', uuid=plan.uuid)

    subjects = Subject.objects.filter(is_active=True)
    context = {'subjects': subjects}
    return render(request, 'ai_core/study_plan_create.html', context)


@login_required
def study_plan_detail(request, uuid):
    """O'quv reja tafsilotlari"""
    plan = get_object_or_404(StudyPlan, uuid=uuid, user=request.user)
    tasks = plan.tasks.all().order_by('scheduled_date', 'order')

    context = {'plan': plan, 'tasks': tasks}
    return render(request, 'ai_core/study_plan_detail.html', context)


@login_required
def study_plan_update(request, uuid):
    """O'quv rejani yangilash"""
    plan = get_object_or_404(StudyPlan, uuid=uuid, user=request.user)

    if request.method == 'POST':
        plan.status = request.POST.get('status', plan.status)
        plan.save()
        messages.success(request, "Reja yangilandi")

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
    """Chat API endpoint"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
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
                title=message[:50]
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
            model_used='claude-3-haiku'
        )

        conversation.message_count = conversation.messages.count()
        conversation.save()

        return JsonResponse({
            'response': ai_response,
            'conversation_uuid': str(conversation.uuid)
        })

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