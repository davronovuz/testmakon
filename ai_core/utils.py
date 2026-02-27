"""
AI Core - Gemini API utility (requests-based, no SDK dependency)
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1/models/"
    "gemini-2.0-flash:generateContent"
)


def get_ai_response(messages_list, system_prompt=None):
    """Gemini REST API bilan bog'lanish (SDK ishlatilmaydi)."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return "AI xizmati hozircha mavjud emas. Iltimos, keyinroq urinib ko'ring."

    if system_prompt is None:
        system_prompt = (
            "Sen TestMakon.uz platformasining AI mentorisan. "
            "Sening vazifang O'zbekistondagi abituriyentlarga universitetga "
            "kirish imtihonlariga tayyorlanishda yordam berish. "
            "O'zbek tilida javob berasan. Javoblaringni qisqa, aniq va foydali qilib ber."
        )

    # Contents ro'yxatini tuzish
    contents = [
        {"role": "user", "parts": [{"text": system_prompt}]},
        {"role": "model", "parts": [{"text": "Tushundim. Sizga yordam berishga tayyorman."}]},
    ]

    for msg in messages_list:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    try:
        resp = requests.post(
            GEMINI_URL,
            params={"key": api_key},
            json={
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048,
                },
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    except requests.exceptions.HTTPError as e:
        logger.error(f"Gemini API HTTP xatolik: {e.response.status_code} — {e.response.text[:200]}")
        return f"AI xatolik: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Gemini API xatolik: {e}")
        return f"Texnik xatolik: {str(e)}"


def get_user_ai_context(user):
    """
    User ma'lumotlari asosida boyitilgan system_prompt qaytaradi.
    AI Mentor barcha suhbatlarda foydalanuvchini taniydi.
    """
    try:
        from tests_app.models import UserSubjectPerformance
        from ai_core.models import WeakTopicAnalysis

        lines = [
            "Sen TestMakon.uz platformasining shaxsiy AI mentorissan.",
            "Sening vazifang O'zbekistondagi abituriyentlarga universitetga kirish imtihonlariga tayyorlanishda yordam berish.",
            "Javoblaringni O'zbek tilida, qisqa, aniq va ilhomlantiradigan qilib ber.",
            "",
            "=== FOYDALANUVCHI PROFILI ===",
            f"Ismi: {user.get_full_name() or user.username}",
        ]

        if hasattr(user, 'education_level') and user.education_level:
            lines.append(f"Ta'lim darajasi: {user.education_level}")
        if hasattr(user, 'region') and user.region:
            lines.append(f"Viloyat: {user.region}")
        if hasattr(user, 'target_university') and user.target_university:
            lines.append(f"Maqsadli universitet: {user.target_university}")
        if hasattr(user, 'target_direction') and user.target_direction:
            lines.append(f"Yo'nalish: {user.target_direction}")

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

        subject_perfs = UserSubjectPerformance.objects.filter(
            user=user
        ).select_related('subject').order_by('average_score')[:6]

        if subject_perfs.exists():
            lines.append("")
            lines.append("=== FAN NATIJALARI ===")
            for sp in subject_perfs:
                emoji = "🔴" if sp.average_score < 50 else ("🟡" if sp.average_score < 75 else "🟢")
                lines.append(f"{emoji} {sp.subject.name}: {sp.average_score:.0f}%")

        weak_topics = WeakTopicAnalysis.objects.filter(
            user=user
        ).select_related('subject', 'topic').order_by('accuracy_rate')[:5]

        if weak_topics.exists():
            lines.append("")
            lines.append("=== SUST MAVZULAR ===")
            for wt in weak_topics:
                lines.append(f"- {wt.subject.name} / {wt.topic.name}: {wt.accuracy_rate:.0f}%")

        lines.append("")
        lines.append("Bu ma'lumotlar asosida foydalanuvchiga shaxsiy, aniq yordam ber.")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"get_user_ai_context xato: {e}")
        return (
            "Sen TestMakon.uz platformasining AI mentorisan. "
            "O'zbek tilida javob berasan."
        )
