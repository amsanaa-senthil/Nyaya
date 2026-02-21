from agent.agno_agent import NyayaAgent
import re

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # remove extra newlines and spaces
    text = text.replace('\xad', '')   # remove OCR soft hyphens
    return text.strip()


if __name__ == "__main__":
    agent = NyayaAgent()

    while True:
   
        user_input = input("\nAsk Nyaya: ")
        query = f"""
        {user_input}

            You are a legal assistant.

            Answer the question using simple and clear English.

            Follow this format strictly:

            1. Direct Answer:
            Give a one-sentence answer (Yes or No + short explanation).

            2. Brief Legal Reasoning:
            - Use bullet points
            - Maximum 5-6 bullet points
            - Use simple English
            - Do NOT copy text from the case
            - Explain the reasoning clearly in your own words
            - Remove any OCR noise
            If the answer is unclear from the context, say so.
        """
        if query.lower() == "exit":
            break

        answer = agent.ask(query)
        print("\nAnswer:\n", answer)

