"""
AI Core - Gemini API utility
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_ai_response(messages_list, system_prompt=None):
    """Gemini API bilan bog'lanish"""
    import google.generativeai as genai

    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return "AI xizmati hozircha mavjud emas. Iltimos, keyinroq urinib ko'ring."

    try:
        genai.configure(api_key=api_key)

        if system_prompt is None:
            system_prompt = """Sen TestMakon.uz platformasining AI mentorisan.
            Sening vazifang O'zbekistondagi abituriyentlarga universitetga kirish imtihonlariga tayyorlanishda yordam berish.
            Sen o'zbek tilida javob berasan. Javoblaringni qisqa, aniq va foydali qilib ber."""

        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=system_prompt)

        chat_history = []
        last_user_message = ""

        for msg in messages_list:
            role = "user" if msg['role'] == "user" else "model"
            content = msg['content']
            if role == "user":
                last_user_message = content
            if msg != messages_list[-1]:
                chat_history.append({"role": role, "parts": [content]})

        chat = model.start_chat(history=chat_history)
        response = chat.send_message(last_user_message)
        return response.text

    except Exception as e:
        logger.error(f"Gemini API xatolik: {e}")
        return f"Texnik xatolik: {str(e)}"


def get_user_ai_context(user):
    """
    User ma'lumotlari asosida boyitilgan system_prompt qaytaradi.
    AI Mentor barcha suhbatlarda foydalanuvchini taniydi.
    """
    try:
        from tests_app.models import UserSubjectPerformance, UserAnalyticsSummary
        from ai_core.models import WeakTopicAnalysis

        lines = [
            "Sen TestMakon.uz platformasining shaxsiy AI mentorissan.",
            "Sening vazifang O'zbekistondagi abituriyentlarga universitetga kirish imtihonlariga tayyorlanishda yordam berish.",
            "Javoblaringni O'zbek tilida, qisqa, aniq va ilhomlantiradigan qilib ber.",
            "",
            f"=== FOYDALANUVCHI PROFILI ===",
            f"Ismi: {user.get_full_name() or user.username}",
        ]

        # Ta'lim ma'lumotlari
        if hasattr(user, 'education_level') and user.education_level:
            lines.append(f"Ta'lim darajasi: {user.education_level}")
        if hasattr(user, 'region') and user.region:
            lines.append(f"Viloyat: {user.region}")

        # Maqsadli universitet
        if hasattr(user, 'target_university') and user.target_university:
            lines.append(f"Maqsadli universitet: {user.target_university}")
        if hasattr(user, 'target_direction') and user.target_direction:
            lines.append(f"Yo'nalish: {user.target_direction}")

        # Analytics summary
        try:
            summary = user.analytics_summary
            if summary.predicted_dtm_score > 0:
                lines.append(f"Bashorat DTM ball: {summary.predicted_dtm_score}/189")
            if summary.overall_accuracy > 0:
                lines.append(f"Umumiy aniqlik: {summary.overall_accuracy}%")
            if summary.total_tests_completed > 0:
                lines.append(f"Jami ishlagan testlar: {summary.total_tests_completed} ta")
            if summary.weak_topics_count > 0:
                lines.append(f"Sust mavzular soni: {summary.weak_topics_count} ta")
        except Exception:
            pass

        # Fan natijalari
        subject_perfs = UserSubjectPerformance.objects.filter(
            user=user
        ).select_related('subject').order_by('average_score')[:6]

        if subject_perfs.exists():
            lines.append("")
            lines.append("=== FAN NATIJALARI ===")
            for sp in subject_perfs:
                emoji = "🔴" if sp.average_score < 50 else ("🟡" if sp.average_score < 75 else "🟢")
                lines.append(f"{emoji} {sp.subject.name}: {sp.average_score:.0f}% (eng yaxshi: {sp.best_score:.0f}%)")

        # Eng sust mavzular
        weak_topics = WeakTopicAnalysis.objects.filter(
            user=user
        ).select_related('subject', 'topic').order_by('accuracy_rate')[:5]

        if weak_topics.exists():
            lines.append("")
            lines.append("=== SUST MAVZULAR (DIQQAT) ===")
            for wt in weak_topics:
                lines.append(f"- {wt.subject.name} / {wt.topic.name}: {wt.accuracy_rate:.0f}% aniqlik")

        lines.append("")
        lines.append("Bu ma'lumotlarni hisobga olgan holda, foydalanuvchiga shaxsiy, aniq va foydali yordam ber.")
        lines.append("Sust mavzularga alohida e'tibor qaratishni tavsiya et.")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"get_user_ai_context xato: user={user.id}, {e}")
        # Fallback — asosiy system prompt
        return """Sen TestMakon.uz platformasining AI mentorisan.
O'zbek tilida javob berasan. Javoblaringni qisqa, aniq va foydali qilib ber."""
