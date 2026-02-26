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
