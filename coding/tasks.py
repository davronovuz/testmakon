"""
TestMakon.uz — Coding Celery Tasks
"""

from celery import shared_task
from django.db.models import F
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def _normalize_output(text):
    """Output normallashtirish — solishtirish uchun"""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.strip().split('\n')]
    while lines and lines[-1] == '':
        lines.pop()
    return '\n'.join(lines)


@shared_task(bind=True, max_retries=2, time_limit=120)
def execute_code_submission(self, submission_id):
    """Kodni Docker sandbox'da ishlatish — barcha test case'lar"""
    from coding.models import CodeSubmission
    from coding.sandbox import DockerSandbox

    try:
        submission = CodeSubmission.objects.select_related('problem', 'language').get(id=submission_id)
    except CodeSubmission.DoesNotExist:
        return

    # Status: running
    submission.status = 'running'
    submission.save(update_fields=['status'])

    sandbox = DockerSandbox()
    problem = submission.problem

    # Test case'larni olish
    if submission.is_sample_run:
        test_cases = problem.test_cases.filter(is_sample=True).order_by('order')
    else:
        test_cases = problem.test_cases.all().order_by('order')

    results = []
    passed = 0
    max_time = 0
    final_status = 'accepted'

    # Test case'larni listga olish — break bo'lganda ham total_count to'g'ri bo'lishi uchun
    test_cases_list = list(test_cases)

    for tc in test_cases_list:
        result = sandbox.execute(
            language=submission.language,
            code=submission.code,
            input_data=tc.input_data,
            time_limit=problem.time_limit,
        )

        # Natijani tekshirish
        if result['error']:
            tc_status = 'internal_error'
            final_status = 'internal_error'
        elif result['timed_out']:
            tc_status = 'time_limit'
            if final_status == 'accepted':
                final_status = 'time_limit'
        elif result['exit_code'] != 0:
            # Compilation vs runtime error ajratish
            if submission.language.compile_cmd and result['stderr']:
                tc_status = 'compilation_error'
            else:
                tc_status = 'runtime_error'
            if final_status == 'accepted':
                final_status = tc_status
        else:
            expected = _normalize_output(tc.expected_output)
            actual = _normalize_output(result['stdout'])
            if actual == expected:
                tc_status = 'accepted'
                passed += 1
            else:
                tc_status = 'wrong_answer'
                if final_status == 'accepted':
                    final_status = 'wrong_answer'

        max_time = max(max_time, result['execution_time'])

        tc_result = {
            'test_case_id': tc.id,
            'order': tc.order,
            'is_sample': tc.is_sample,
            'status': tc_status,
            'execution_time': result['execution_time'],
            'stdout': result['stdout'][:1000] if tc.is_sample else '',
            'stderr': result['stderr'][:500] if tc.is_sample else '',
            'expected': tc.expected_output[:500] if tc.is_sample else '',
            'input': tc.input_data[:500] if tc.is_sample else '',
        }
        results.append(tc_result)

        # Compilation error — barchasida bir xil, to'xtatish
        if tc_status in ('compilation_error', 'internal_error'):
            submission.error_message = result['stderr'] or result['error'] or ''
            break

    # Saqlash
    submission.results = results
    submission.passed_count = passed
    submission.total_count = len(test_cases_list)
    submission.execution_time = max_time
    submission.status = final_status
    submission.save(update_fields=[
        'results', 'passed_count', 'total_count',
        'execution_time', 'status', 'error_message'
    ])

    # Stats yangilash (faqat to'liq submit uchun, sample run emas)
    if not submission.is_sample_run:
        _update_problem_stats(submission)
        _update_user_stats(submission)


def _update_problem_stats(submission):
    """Masala statistikasini atomik yangilash"""
    from coding.models import CodingProblem

    updates = {'total_submissions': F('total_submissions') + 1}
    if submission.status == 'accepted':
        updates['accepted_submissions'] = F('accepted_submissions') + 1

    CodingProblem.objects.filter(id=submission.problem_id).update(**updates)


def _update_user_stats(submission):
    """Foydalanuvchi statistikasini yangilash"""
    from coding.models import UserCodingStats, CodeSubmission

    stats, _ = UserCodingStats.objects.get_or_create(user=submission.user)

    # Total submissions
    stats.total_submissions = F('total_submissions') + 1
    stats.save(update_fields=['total_submissions'])
    stats.refresh_from_db()

    # Bu masala birinchi marta yechildimi?
    if submission.status == 'accepted':
        already_solved = CodeSubmission.objects.filter(
            user=submission.user,
            problem=submission.problem,
            status='accepted',
            is_sample_run=False,
        ).exclude(id=submission.id).exists()

        if not already_solved:
            # Yangi yechim
            difficulty = submission.problem.difficulty
            updates = {'problems_solved': F('problems_solved') + 1}
            if difficulty == 'easy':
                updates['easy_solved'] = F('easy_solved') + 1
            elif difficulty == 'medium':
                updates['medium_solved'] = F('medium_solved') + 1
            elif difficulty == 'hard':
                updates['hard_solved'] = F('hard_solved') + 1

            UserCodingStats.objects.filter(id=stats.id).update(**updates)

            # Streak
            today = timezone.now().date()
            if stats.last_solved_date != today:
                if stats.last_solved_date and (today - stats.last_solved_date).days == 1:
                    new_streak = stats.current_streak + 1
                else:
                    new_streak = 1
                UserCodingStats.objects.filter(id=stats.id).update(
                    current_streak=new_streak,
                    max_streak=max(new_streak, stats.max_streak),
                    last_solved_date=today,
                )

        # Attempted count
        attempted = CodeSubmission.objects.filter(
            user=submission.user,
            is_sample_run=False,
        ).values('problem').distinct().count()
        UserCodingStats.objects.filter(id=stats.id).update(problems_attempted=attempted)

        # Language stats
        stats.refresh_from_db()
        lang_name = submission.language.slug
        lang_stats = stats.language_stats or {}
        if lang_name not in lang_stats:
            lang_stats[lang_name] = {'solved': 0, 'submitted': 0}
        lang_stats[lang_name]['submitted'] += 1
        if submission.status == 'accepted' and not already_solved:
            lang_stats[lang_name]['solved'] += 1
        stats.language_stats = lang_stats
        stats.save(update_fields=['language_stats'])


@shared_task
def cleanup_old_containers():
    """Eski Docker konteynerlarni tozalash — har 30 daqiqada"""
    from coding.sandbox import DockerSandbox
    sandbox = DockerSandbox()
    removed = sandbox.cleanup_old_containers()
    logger.info(f"Tozalandi: {removed} ta konteyner")
