"""
AI Core - StudyPlanService
Barcha biznes logika shu yerda. Celery/Django framework dan mustaqil.
Alohida test qilish, qayta ishlatish, debug qilish mumkin.
"""
import json
import re
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class StudyPlanService:
    """
    AI o'quv reja yaratish xizmati.

    Arxitektura:
        Celery task (thin) → StudyPlanService.run() → Gemini API + DB

    Foydalanish:
        service = StudyPlanService(plan_id, progress_callback=fn)
        tasks_created = service.run()
    """

    def __init__(self, plan_id, progress_callback=None):
        self.plan_id = plan_id
        # progress_callback(percent: int, step: str)
        self._cb = progress_callback or (lambda p, s: None)

    # ------------------------------------------------------------------ #
    #  Asosiy metod                                                        #
    # ------------------------------------------------------------------ #

    def run(self):
        from .models import StudyPlan, StudyPlanTask
        from tests_app.models import TestAttempt
        from ai_core.models import WeakTopicAnalysis

        self._cb(10, "Foydalanuvchi ma'lumotlari o'qilmoqda")

        plan = StudyPlan.objects.get(id=self.plan_id)
        user = plan.user
        subjects = list(plan.subjects.all())
        today = timezone.localdate()

        if not subjects:
            logger.warning(f"Plan {self.plan_id}: fan tanlanmagan")
            return 0

        # 1 — Fan bo'yicha so'nggi natijalar
        subject_stats = self._collect_subject_stats(user)

        self._cb(25, "Sust mavzular aniqlanmoqda")

        # 2 — Sust mavzular (top 5 — kichik prompt)
        weak_data = [
            {
                'fan': wt.subject.name,
                'mavzu': wt.topic.name,
                'aniqlik': round(wt.accuracy_rate, 1),
            }
            for wt in WeakTopicAnalysis.objects.filter(
                user=user, subject__in=subjects
            ).select_related('subject', 'topic').order_by('accuracy_rate')[:5]
        ]

        # 3 — Reja parametrlari
        if plan.target_exam_date and plan.target_exam_date > today:
            total_days = (plan.target_exam_date - today).days
        else:
            total_days = 28
        weekly_days = max(1, min(7, plan.weekly_days))
        num_weeks = max(1, (total_days + 6) // 7)

        self._cb(45, "AI haftalik shablon yaratmoqda")

        # 4 — AI dan 1 haftalik shablon so'rash
        week_template, ai_analysis = self._generate_weekly_template(
            plan, subjects, subject_stats, weak_data, weekly_days
        )

        # AI muvaffaqiyatsiz bo'lsa — fallback
        if not week_template:
            logger.warning(f"Plan {self.plan_id}: AI shablon qaytarmadi — fallback")
            self._cb(70, "Asosiy reja tuzilmoqda")
            tasks_created = self._create_basic_tasks(
                plan, subjects, today, total_days, weekly_days
            )
            plan.is_ai_generated = False
            plan.total_tasks = tasks_created
            plan.save(update_fields=['total_tasks', 'is_ai_generated'])
            self._cb(100, f"Tayyor! {tasks_created} ta vazifa yaratildi")
            return tasks_created

        self._cb(65, f"Shablon {num_weeks} haftaga kengaytirilmoqda")

        # 5 — Shablonni butun muddatga takrorlash
        tasks_created = self._expand_and_save(
            plan, week_template, subjects, today, total_days, weekly_days, num_weeks
        )

        self._cb(90, "Natijalar saqlanmoqda")

        plan.total_tasks = tasks_created
        plan.is_ai_generated = True
        plan.ai_analysis = ai_analysis
        plan.save(update_fields=['total_tasks', 'is_ai_generated', 'ai_analysis'])

        # Fallback: agar hech narsa yaratilmagan bo'lsa
        if tasks_created == 0:
            logger.warning(f"Plan {self.plan_id}: 0 ta vazifa — basic fallback")
            tasks_created = self._create_basic_tasks(
                plan, subjects, today, total_days, weekly_days
            )
            plan.total_tasks = tasks_created
            plan.is_ai_generated = False
            plan.save(update_fields=['total_tasks', 'is_ai_generated'])

        self._cb(100, f"Tayyor! {tasks_created} ta vazifa yaratildi")
        logger.info(
            f"StudyPlanService OK: plan={self.plan_id}, "
            f"{tasks_created} vazifa, {num_weeks} hafta"
        )
        return tasks_created

    # ------------------------------------------------------------------ #
    #  Yordamchi metodlar                                                  #
    # ------------------------------------------------------------------ #

    def _collect_subject_stats(self, user):
        from tests_app.models import TestAttempt
        stats = {}
        for attempt in TestAttempt.objects.filter(
            user=user, status='completed'
        ).select_related('test__subject').order_by('-completed_at')[:20]:
            subj = attempt.test.subject if attempt.test else None
            if not subj:
                continue
            key = subj.name
            if key not in stats:
                stats[key] = []
            stats[key].append(attempt.percentage)

        return {
            k: {'avg': round(sum(v) / len(v), 1), 'count': len(v)}
            for k, v in stats.items()
        }

    def _generate_weekly_template(
        self, plan, subjects, subject_stats, weak_data, weekly_days
    ):
        """
        Gemini API dan 1 haftalik shablon so'rash.
        Qaytaradi: (week_template list, ai_analysis str)
        Muvaffaqiyatsiz bo'lsa: (None, '')
        """
        from .utils import get_ai_response

        subject_names = [s.name for s in subjects]
        day_names = [
            'Dushanba', 'Seshanba', 'Chorshanba',
            'Payshanba', 'Juma', 'Shanba', 'Yakshanba',
        ]
        active_days = day_names[:weekly_days]

        system_prompt = (
            "Sen TestMakon.uz AI o'quv reja tuzuvchisan. "
            "Javobni FAQAT sof JSON formatida ber, boshqa hech narsa yozma."
        )

        user_prompt = f"""Foydalanuvchi:
- Fanlar: {', '.join(subject_names)}
- Kunlik o'qish: {plan.daily_hours} soat
- Dars kunlari: {', '.join(active_days)} (jami {weekly_days} kun)
- Maqsad ball: {plan.target_score or 'DTM'}
- Fan natijalari: {json.dumps(subject_stats, ensure_ascii=False)}
- Ustuvor sust mavzular: {json.dumps(weak_data, ensure_ascii=False)}

Faqat 1 haftalik shablon tuz — {weekly_days} ta vazifa (har dars kuni uchun 1 ta).
Sust mavzularga e'tibor ber. study/practice/review/test larni aralashtirib ishlat.
day_index: 0={active_days[0]} ... {weekly_days - 1}={active_days[-1]}

JSON format (boshqa hech narsa yozma):
{{
  "analysis": "2 gaplik tahlil",
  "week_template": [
    {{
      "day_index": 0,
      "title": "Qisqa sarlavha",
      "subject": "Fan nomi (ro'yxatdan biri)",
      "task_type": "study|practice|review|test",
      "difficulty": "easy|medium|hard",
      "minutes": {int(plan.daily_hours * 60)},
      "notes": "Nega bu muhim — 1 gap",
      "is_weak_topic": false
    }}
  ]
}}"""

        try:
            response = get_ai_response(
                [{"role": "user", "content": user_prompt}], system_prompt
            )
            match = re.search(r'\{[\s\S]*\}', response)
            if not match:
                logger.error(f"Plan {self.plan_id}: AI JSON qaytarmadi")
                return None, ''

            data = json.loads(match.group())
            template = data.get('week_template', [])
            analysis = data.get('analysis', '')

            if not template:
                logger.error(f"Plan {self.plan_id}: week_template bo'sh")
                return None, analysis

            logger.info(f"Plan {self.plan_id}: AI {len(template)} ta haftalik vazifa qaytardi")
            return template, analysis

        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Plan {self.plan_id}: _generate_weekly_template xato — {e}")
            return None, ''

    def _expand_and_save(
        self, plan, week_template, subjects, today, total_days, weekly_days, num_weeks
    ):
        """Shablonni butun muddatga takrorlab, DB ga saqlaydi."""
        from .models import StudyPlanTask

        subject_map = {s.name.lower(): s for s in subjects}
        tasks_to_create = []
        order = 0

        for week_num in range(num_weeks):
            for item in week_template:
                day_index = int(item.get('day_index', 0))
                if day_index >= weekly_days:
                    continue

                day_offset = week_num * 7 + day_index
                scheduled = today + timedelta(days=day_offset)
                if scheduled > today + timedelta(days=total_days):
                    break

                subj_obj = self._resolve_subject(
                    item.get('subject', ''), subject_map, subjects, order
                )

                tasks_to_create.append(
                    StudyPlanTask(
                        study_plan=plan,
                        title=item.get('title', "O'quv vazifasi"),
                        task_type=item.get('task_type', 'practice'),
                        subject=subj_obj,
                        scheduled_date=scheduled,
                        estimated_minutes=int(item.get('minutes', 45)),
                        questions_count=(
                            10 if item.get('task_type') in ('test', 'practice') else None
                        ),
                        ai_notes=item.get('notes', ''),
                        difficulty=item.get('difficulty', 'medium'),
                        weak_topic_focus=bool(item.get('is_weak_topic', False)),
                        order=order,
                    )
                )
                order += 1

        # Batch insert
        StudyPlanTask.objects.bulk_create(tasks_to_create)
        return len(tasks_to_create)

    def _resolve_subject(self, name_raw, subject_map, subjects, fallback_idx):
        """Fan nomini DB obyektiga moslashtiradi."""
        name = name_raw.lower().strip()
        if name in subject_map:
            return subject_map[name]
        for k, v in subject_map.items():
            if k in name or name in k:
                return v
        return subjects[fallback_idx % len(subjects)] if subjects else None

    def _create_basic_tasks(self, plan, subjects, today, total_days, weekly_days):
        """AI ishlamasa standart haftalik jadval yaratadi."""
        from .models import StudyPlanTask

        CYCLE = ['study', 'practice', 'review', 'test', 'practice', 'study', 'review']
        tasks = []
        idx = 0
        for day_offset in range(total_days):
            current_date = today + timedelta(days=day_offset)
            if current_date.weekday() >= weekly_days:
                continue
            subject = subjects[idx % len(subjects)]
            task_type = CYCLE[idx % len(CYCLE)]
            tasks.append(
                StudyPlanTask(
                    study_plan=plan,
                    title=f"{subject.name} — {task_type}",
                    task_type=task_type,
                    subject=subject,
                    scheduled_date=current_date,
                    estimated_minutes=max(30, int(plan.daily_hours * 60 // 2)),
                    questions_count=10 if task_type in ('test', 'practice') else None,
                    difficulty='medium',
                    order=idx,
                )
            )
            idx += 1

        StudyPlanTask.objects.bulk_create(tasks)
        plan.total_tasks = len(tasks)
        plan.save(update_fields=['total_tasks'])
        return len(tasks)
