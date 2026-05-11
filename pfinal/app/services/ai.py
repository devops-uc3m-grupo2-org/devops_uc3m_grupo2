import os

from google import genai
from google.genai import types

_SYNONYMS: dict[str, list[str]] = {
    "economía": ["finanzas", "bolsa", "mercado", "negocios", "inversión"],
    "política": ["gobierno", "parlamento", "elecciones", "partido", "legislación"],
    "tecnología": ["innovación", "inteligencia artificial", "software", "digital", "startups"],
    "salud": ["medicina", "sanidad", "enfermedad", "hospital", "tratamiento"],
    "deporte": ["fútbol", "baloncesto", "atletismo", "competición", "liga"],
    "cultura": ["arte", "música", "cine", "teatro", "literatura"],
    "medioambiente": ["clima", "sostenibilidad", "energía", "contaminación", "reciclaje"],
    "educación": ["universidad", "enseñanza", "escuela", "formación", "investigación"],
    "sociedad": ["comunidad", "bienestar", "desigualdad", "familia", "ciudadanía"],
    "ciencia": ["investigación", "descubrimiento", "laboratorio", "experimento", "física"],
}


def _fallback_synonyms(keyword: str) -> list[str]:
    base = keyword.lower().strip()
    related = _SYNONYMS.get(base, [base + " noticias", base + " actualidad"])
    seen: set[str] = set()
    result: list[str] = []
    for term in [base] + related:
        if term not in seen:
            seen.add(term)
            result.append(term)
    return result


def generate_synonyms(keyword: str) -> list[str]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return _fallback_synonyms(keyword)

    try:
        client = genai.Client(api_key=api_key)
        prompt = (
            f"Dame entre 3 y 10 sinónimos o palabras relacionadas con '{keyword}' "
            "en español, útiles para monitorizar noticias. "
            "Responde SOLO con las palabras separadas por comas, sin explicaciones ni puntuación adicional."
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=100,
            ),
        )
        raw = response.text.strip()
        terms = [t.strip().lower() for t in raw.split(",") if t.strip()]
        base = keyword.lower().strip()
        seen: set[str] = set()
        result: list[str] = []
        for term in [base] + terms:
            if term and term not in seen:
                seen.add(term)
                result.append(term)
        return result[:11]  # keyword + hasta 10 sugerencias
    except Exception:
        return _fallback_synonyms(keyword)
