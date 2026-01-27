"""
TestMakon.uz - AI Engine
Kuchsiz mavzularni aniqlash, tavsiyalar va kunlik reja generatsiyasi
"""

from django.utils import timezone
from django.db.models import Avg, Count, Sum, F
from datetime import timedelta

from .models import (
    Subject, Topic, Question, TestAttempt, AttemptAnswer,
    UserTopicPerformance, UserSubjectPerformance,
    DailyUserStats, UserAnalyticsSummary, UserActivityLog
)


class AIEngine:
    """AI tahlil va tavsiyalar"""

    def __init__(self, user):
        self.user = user

    # ==========================================
    # KUCHSIZ/KUCHLI MAVZULARNI ANIQLASH
    # ==========================================

    def get_weak_topics(self, limit=5):
        """Kuchsiz mavzularni olish"""
        return UserTopicPerformance.objects.filter(
            user=self.user,
            total_questions__gte=5,  # kamida 5 ta savol yechgan
            is_weak=True
        ).select_related('topic', 'subject').order_by('current_score')[:limit]

    def get_strong_topics(self, limit=5):
        """Kuchli mavzularni olish"""
        return UserTopicPerformance.objects.filter(
            user=self.user,
            total_questions__gte=5,
            is_strong=True
        ).select_related('topic', 'subject').order_by('-current_score')[:limit]

    def get_topics_to_practice(self, limit=5):
        """Mashq qilish kerak bo'lgan mavzular"""
        # Uzoq vaqt mashq qilinmagan + kuchsiz
        week_ago = timezone.now() - timedelta(days=7)

        return UserTopicPerformance.objects.filter(
            user=self.user,
            total_questions__gte=3
        ).filter(
            last_practiced__lt=week_ago
        ).select_related('topic', 'subject').order_by('current_score')[:limit]

    def get_untouched_topics(self, subject=None, limit=10):
        """Hali yechilmagan mavzular"""
        practiced_topic_ids = UserTopicPerformance.objects.filter(
            user=self.user
        ).values_list('topic_id', flat=True)

        topics = Topic.objects.filter(is_active=True).exclude(id__in=practiced_topic_ids)

        if subject:
            topics = topics.filter(subject=subject)

        return topics[:limit]

    # ==========================================
    # KUNLIK REJA GENERATSIYASI
    # ==========================================

    def generate_daily_plan(self):
        """Kunlik o'qish rejasini generatsiya qilish"""
        plan = {
            'date': timezone.now().date(),
            'tasks': [],
            'estimated_time': 0,
            'target_questions': 0,
        }

        # 1. Kuchsiz mavzulardan savollar (60%)
        weak_topics = self.get_weak_topics(3)
        for perf in weak_topics:
            questions_count = 10 if perf.current_score < 40 else 7
            plan['tasks'].append({
                'type': 'weak_topic',
                'topic': perf.topic,
                'subject': perf.subject,
                'questions': questions_count,
                'reason': f"{perf.current_score}% — yaxshilash kerak",
                'priority': 'high',
                'estimated_time': questions_count * 2,  # daqiqa
            })
            plan['target_questions'] += questions_count
            plan['estimated_time'] += questions_count * 2

        # 2. Uzoq vaqt mashq qilinmagan (20%)
        old_topics = self.get_topics_to_practice(2)
        for perf in old_topics:
            plan['tasks'].append({
                'type': 'review',
                'topic': perf.topic,
                'subject': perf.subject,
                'questions': 5,
                'reason': f"Oxirgi mashq: {perf.last_practiced.strftime('%d.%m') if perf.last_practiced else 'Nomalum'}",
                'priority': 'medium',
                'estimated_time': 10,
            })
            plan['target_questions'] += 5
            plan['estimated_time'] += 10

        # 3. Kuchli mavzularni mustahkamlash (20%)
        strong_topics = self.get_strong_topics(1)
        for perf in strong_topics:
            plan['tasks'].append({
                'type': 'strengthen',
                'topic': perf.topic,
                'subject': perf.subject,
                'questions': 5,
                'reason': f"{perf.current_score}% — mustahkamlash",
                'priority': 'low',
                'estimated_time': 10,
            })
            plan['target_questions'] += 5
            plan['estimated_time'] += 10

        return plan

    # ==========================================
    # ENG YAXSHI O'QISH VAQTINI ANIQLASH
    # ==========================================

    def get_best_study_time(self):
        """Foydalanuvchi eng samarali o'qiydigan vaqtni aniqlash"""
        # Oxirgi 30 kunlik ma'lumot
        month_ago = timezone.now() - timedelta(days=30)

        daily_stats = DailyUserStats.objects.filter(
            user=self.user,
            date__gte=month_ago.date()
        )

        # Soatlar bo'yicha to'plash
        hourly_performance = {}

        for stat in daily_stats:
            if stat.activity_hours:
                for hour, count in stat.activity_hours.items():
                    if hour not in hourly_performance:
                        hourly_performance[hour] = {'sessions': 0, 'accuracy': []}
                    hourly_performance[hour]['sessions'] += count

        # Savollar bo'yicha aniqlikni olish
        answers = AttemptAnswer.objects.filter(
            attempt__user=self.user,
            answered_at__gte=month_ago
        )

        for answer in answers:
            hour = str(answer.answered_at.hour)
            if hour in hourly_performance:
                hourly_performance[hour]['accuracy'].append(1 if answer.is_correct else 0)

        # Eng yaxshi soatlarni aniqlash
        best_hours = []
        for hour, data in hourly_performance.items():
            if data['accuracy']:
                avg_accuracy = sum(data['accuracy']) / len(data['accuracy']) * 100
                if avg_accuracy >= 60 and data['sessions'] >= 3:
                    best_hours.append({
                        'hour': int(hour),
                        'accuracy': round(avg_accuracy, 1),
                        'sessions': data['sessions']
                    })

        best_hours.sort(key=lambda x: x['accuracy'], reverse=True)

        return best_hours[:3]

    # ==========================================
    # CHARCHASH VAQTINI ANIQLASH
    # ==========================================

    def get_fatigue_threshold(self):
        """Qachon charchashni aniqlash (daqiqada)"""
        # Sessionlar davomida aniqlik o'zgarishini kuzatish
        sessions = TestAttempt.objects.filter(
            user=self.user,
            status='completed',
            time_spent__gte=600  # kamida 10 daqiqa
        ).order_by('-started_at')[:20]

        if sessions.count() < 5:
            return 45  # default

        # O'rtacha session davomiyligini hisoblash
        avg_duration = sessions.aggregate(avg=Avg('time_spent'))['avg'] or 2700

        # Agar o'rtacha 45 daqiqadan keyin aniqlik pasaysa
        return min(int(avg_duration / 60), 60)

    # ==========================================
    # UNIVERSITET BASHORATI
    # ==========================================

    def predict_university_match(self):
        """Universitet kirish ehtimolini bashorat qilish"""
        from universities.models import University, Direction

        # Foydalanuvchi o'rtacha bali
        subject_perfs = UserSubjectPerformance.objects.filter(user=self.user)

        if not subject_perfs.exists():
            return []

        # O'rtacha ballni hisoblash (DTM formatida)
        total_score = 0
        subjects_count = 0

        for perf in subject_perfs:
            # 100 ballik tizimdan 189 ballik tizimga o'tkazish (taxminiy)
            dtm_score = (perf.average_score / 100) * 189
            total_score += dtm_score
            subjects_count += 1

        if subjects_count == 0:
            return []

        predicted_score = total_score / subjects_count

        # Universitetlarni topish
        predictions = []

        try:
            directions = Direction.objects.filter(
                is_active=True
            ).select_related('university')

            for direction in directions:
                if direction.passing_score:
                    probability = self._calculate_probability(predicted_score, direction.passing_score)
                    if probability >= 20:
                        predictions.append({
                            'university': direction.university.name,
                            'direction': direction.name,
                            'passing_score': direction.passing_score,
                            'predicted_score': round(predicted_score, 1),
                            'probability': probability,
                            'gap': round(predicted_score - direction.passing_score, 1)
                        })
        except:
            pass

        predictions.sort(key=lambda x: x['probability'], reverse=True)
        return predictions[:10]

    def _calculate_probability(self, user_score, passing_score):
        """Kirish ehtimolini hisoblash"""
        diff = user_score - passing_score

        if diff >= 20:
            return 95
        elif diff >= 10:
            return 85
        elif diff >= 5:
            return 75
        elif diff >= 0:
            return 60
        elif diff >= -5:
            return 45
        elif diff >= -10:
            return 30
        elif diff >= -20:
            return 20
        else:
            return 10

    # ==========================================
    # PROGRESS DINAMIKASI
    # ==========================================

    def get_progress_trend(self, days=14):
        """Oxirgi N kunlik progress"""
        start_date = timezone.now().date() - timedelta(days=days)

        daily_stats = DailyUserStats.objects.filter(
            user=self.user,
            date__gte=start_date
        ).order_by('date')

        trend = []
        for stat in daily_stats:
            trend.append({
                'date': stat.date.strftime('%d.%m'),
                'questions': stat.questions_answered,
                'accuracy': stat.accuracy_rate,
                'time': stat.total_time_spent // 60,  # daqiqada
                'xp': stat.xp_earned,
            })

        return trend

    def get_streak_info(self):
        """Streak ma'lumotlari"""
        today = timezone.now().date()
        streak = 0

        # Ketma-ket kunlarni sanash
        for i in range(365):
            check_date = today - timedelta(days=i)
            has_activity = DailyUserStats.objects.filter(
                user=self.user,
                date=check_date,
                questions_answered__gt=0
            ).exists()

            if has_activity:
                streak += 1
            else:
                if i == 0:  # Bugun hali faollik yo'q
                    continue
                break

        return {
            'current': streak,
            'today_done': DailyUserStats.objects.filter(
                user=self.user,
                date=today,
                questions_answered__gt=0
            ).exists()
        }

    # ==========================================
    # TAVSIYALAR GENERATSIYASI
    # ==========================================

    def generate_recommendations(self):
        """Barcha tavsiyalarni generatsiya qilish"""
        recommendations = []

        # 1. Kuchsiz mavzular
        weak = self.get_weak_topics(3)
        for perf in weak:
            recommendations.append({
                'type': 'weak_topic',
                'priority': 'high',
                'title': f"{perf.topic.name} mavzusini yaxshilang",
                'message': f"Bu mavzuda {perf.current_score}% natija. Bugun 10 ta savol yechsangiz, tez orada yaxshilanadi.",
                'action_url': f"/tests/topic/{perf.subject.slug}/{perf.topic.slug}/",
                'action_text': 'Boshlash',
            })

        # 2. Streak
        streak_info = self.get_streak_info()
        if not streak_info['today_done']:
            recommendations.append({
                'type': 'streak',
                'priority': 'medium',
                'title': f"Streak ni yo'qotmang! ({streak_info['current']} kun)",
                'message': "Bugun hali test yechmadingiz. Kamida 5 ta savol yeching.",
                'action_url': '/tests/quick/',
                'action_text': 'Tezkor test',
            })

        # 3. O'qish vaqti
        best_hours = self.get_best_study_time()
        if best_hours:
            current_hour = timezone.now().hour
            best_hour = best_hours[0]['hour']
            if abs(current_hour - best_hour) <= 1:
                recommendations.append({
                    'type': 'study_time',
                    'priority': 'medium',
                    'title': "Eng samarali vaqtingiz!",
                    'message': f"Siz odatda {best_hour}:00 da yaxshi natija ko'rsatasiz. Hozir o'qish uchun eng yaxshi vaqt!",
                    'action_url': '/tests/',
                    'action_text': 'Test boshlash',
                })

        # 4. Uzoq vaqt mashq qilinmagan
        old_topics = self.get_topics_to_practice(2)
        for perf in old_topics:
            days_ago = (timezone.now() - perf.last_practiced).days if perf.last_practiced else 30
            recommendations.append({
                'type': 'review',
                'priority': 'low',
                'title': f"{perf.topic.name} ni takrorlang",
                'message': f"{days_ago} kun oldin mashq qilgansiz. Unutmaslik uchun takrorlang.",
                'action_url': f"/tests/topic/{perf.subject.slug}/{perf.topic.slug}/",
                'action_text': 'Takrorlash',
            })

        return recommendations

    # ==========================================
    # UMUMIY DASHBOARD DATA
    # ==========================================

    def get_dashboard_data(self):
        """Dashboard uchun barcha ma'lumotlar"""
        return {
            'weak_topics': list(self.get_weak_topics(5).values(
                'topic__name', 'subject__name', 'current_score', 'total_questions'
            )),
            'strong_topics': list(self.get_strong_topics(3).values(
                'topic__name', 'subject__name', 'current_score'
            )),
            'daily_plan': self.generate_daily_plan(),
            'best_study_hours': self.get_best_study_time(),
            'fatigue_threshold': self.get_fatigue_threshold(),
            'progress_trend': self.get_progress_trend(14),
            'streak': self.get_streak_info(),
            'recommendations': self.generate_recommendations(),
            'university_predictions': self.predict_university_match()[:5],
        }