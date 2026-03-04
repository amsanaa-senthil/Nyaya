# agent/llm.py

from openai import AzureOpenAI
from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION
)

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=AZURE_OPENAI_API_VERSION
)

def generate_answer(prompt):
    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
