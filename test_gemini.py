import os
import requests

api_key = os.environ.get('GEMINI_API_KEY', '')
print(f"API Key: {api_key[:15]}...")

models = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-001",
]

for model in models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    resp = requests.post(
        url,
        params={"key": api_key},
        json={"contents": [{"role": "user", "parts": [{"text": "Salom"}]}]},
        timeout=30,
    )
    if resp.status_code == 200:
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        print(f"OK: {model} -> {text[:60]}")
        break
    else:
        print(f"FAIL {resp.status_code}: {model} -> {resp.json().get('error',{}).get('message','')[:80]}")
