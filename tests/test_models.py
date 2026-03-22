"""Manual model-listing helper for Gemini account checks."""

import os

from dotenv import load_dotenv


def run_manual_model_list() -> None:
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    try:
        # Preferred SDK (google-genai)
        from google import genai  # type: ignore

        client = genai.Client(api_key=api_key)
        for model in client.models.list():
            print(getattr(model, "name", "unknown"))
        return
    except Exception:
        pass

    # Backward-compatible fallback for older environments.
    import google.generativeai as legacy_genai  # type: ignore

    legacy_genai.configure(api_key=api_key)
    for model in legacy_genai.list_models():
        print(getattr(model, "name", "unknown"))


def test_models_smoke_placeholder():
    assert True


if __name__ == "__main__":
    run_manual_model_list()
