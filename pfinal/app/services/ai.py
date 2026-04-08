import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_synonyms(keyword: str) -> list[str]:
    prompt = f"""
    Dame sinónimos o términos relacionados con "{keyword}".
    Devuelve solo una lista separada por comas.
    """

    model = genai.GenerativeModel("models/gemini-pro")
    response = model.generate_content(prompt)

    text = response.text

    return [t.strip().lower() for t in text.split(",") if t.strip()]