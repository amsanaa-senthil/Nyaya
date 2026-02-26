# agent/llm.py

import os
from google import genai
from config import GEMINI_API_KEY

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_answer(prompt):
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    return response.text
