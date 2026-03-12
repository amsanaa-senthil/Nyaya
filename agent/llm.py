# agent/llm.py

import os
from typing import Any, Optional
from dotenv import load_dotenv
from resilience import CircuitBreaker, call_with_retry

load_dotenv()

# Try Azure OpenAI first, fallback to Gemini
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-35-turbo")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Initialize the appropriate client
llm_backend: Optional[str] = None
client: Any = None
azure_client: Any = None
gemini_client: Any = None
azure_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
gemini_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)

if AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT:
    try:
        from openai import AzureOpenAI
        azure_client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION
        )
        client = azure_client
        llm_backend = "azure"
        print("[LLM] Using Azure OpenAI")
    except Exception as e:
        print(f"[LLM] Azure OpenAI init failed: {e}")

if not llm_backend and GEMINI_API_KEY:
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=GEMINI_API_KEY)  # type: ignore
        gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp')  # type: ignore
        client = gemini_client
        llm_backend = "gemini"
        print("[LLM] Using Gemini (free)")
    except Exception as e:
        print(f"[LLM] Gemini init failed: {e}")

if not llm_backend:
    print("[WARNING] No LLM configured! Set AZURE_OPENAI_API_KEY or GEMINI_API_KEY in .env")
    print("Get free Gemini key: https://makersuite.google.com/app/apikey")


def generate_answer(prompt):
    """Generate natural language answer using configured LLM"""
    if not llm_backend:
        raise RuntimeError(
            "No LLM configured. Set AZURE_OPENAI_API_KEY or GEMINI_API_KEY in .env\n"
            "Get free Gemini key: https://makersuite.google.com/app/apikey"
        )
    
    try:
        if llm_backend == "azure":
            def _extract_text(resp: Any) -> tuple[str, Optional[str]]:
                if not resp.choices:
                    return "", None
                choice = resp.choices[0]
                finish_reason = getattr(choice, "finish_reason", None)
                message_content = choice.message.content

                if isinstance(message_content, str) and message_content.strip():
                    return message_content.strip(), finish_reason

                if isinstance(message_content, list):
                    text_parts = []
                    for part in message_content:
                        if isinstance(part, dict):
                            text = part.get("text")
                            if isinstance(text, str) and text.strip():
                                text_parts.append(text.strip())
                        else:
                            text = getattr(part, "text", None)
                            if isinstance(text, str) and text.strip():
                                text_parts.append(text.strip())
                    if text_parts:
                        return "\n".join(text_parts), finish_reason

                return "", finish_reason

            active_client = azure_client or client
            response = call_with_retry(
                active_client.chat.completions.create,  # type: ignore
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[{"role": "user", "content": prompt}],
                temperature=1,
                max_completion_tokens=1400,
                retries=2,
                timeout_seconds=25,
                circuit_breaker=azure_breaker,
            )
            extracted_text, finish_reason = _extract_text(response)
            if extracted_text:
                return extracted_text

            if finish_reason == "length":
                retry_response = call_with_retry(
                    active_client.chat.completions.create,  # type: ignore
                    model=AZURE_OPENAI_DEPLOYMENT,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1,
                    max_completion_tokens=4000,
                    retries=1,
                    timeout_seconds=35,
                    circuit_breaker=azure_breaker,
                )
                retry_text, _ = _extract_text(retry_response)
                if retry_text:
                    return retry_text

            # Fallback for models that can return empty content in chat completions
            # while still being able to produce text via Responses API.
            try:
                fallback = call_with_retry(
                    active_client.responses.create,  # type: ignore
                    model=AZURE_OPENAI_DEPLOYMENT,
                    input=prompt,
                    max_output_tokens=800,
                    retries=1,
                    timeout_seconds=25,
                    circuit_breaker=azure_breaker,
                )
                output_text = getattr(fallback, "output_text", None)
                if isinstance(output_text, str) and output_text.strip():
                    return output_text.strip()
            except Exception:
                # Azure path failed; attempt Gemini fallback if available.
                if gemini_client:
                    gemini_response = call_with_retry(
                        gemini_client.generate_content,  # type: ignore
                        prompt,
                        retries=1,
                        timeout_seconds=25,
                        circuit_breaker=gemini_breaker,
                    )
                    text = getattr(gemini_response, "text", None)
                    if isinstance(text, str) and text.strip():
                        return text.strip()

            raise RuntimeError("Azure returned an empty response")
        
        elif llm_backend == "gemini":
            active_client = gemini_client or client
            response = call_with_retry(
                active_client.generate_content,  # type: ignore
                prompt,
                retries=2,
                timeout_seconds=25,
                circuit_breaker=gemini_breaker,
            )
            return response.text
    
    except Exception as e:
        raise RuntimeError(f"LLM generation failed ({llm_backend}): {str(e)}")
