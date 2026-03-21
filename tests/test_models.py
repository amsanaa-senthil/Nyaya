"""Manual model-listing helper for Gemini account checks."""

import os

from dotenv import load_dotenv
import google.generativeai as genai


def run_manual_model_list() -> None:
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    for model in genai.list_models():
        print(getattr(model, "name", "unknown"))


def test_models_smoke_placeholder():
    assert True


if __name__ == "__main__":
    run_manual_model_list()
