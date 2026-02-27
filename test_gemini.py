import os
import requests

api_key = os.environ.get('GEMINI_API_KEY', '')
print(f"API Key: {api_key[:15]}...")

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

resp = requests.post(
    url,
    params={"key": api_key},
    json={"contents": [{"role": "user", "parts": [{"text": "Salom, sen kimsan?"}]}]},
    timeout=30,
)

print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")
