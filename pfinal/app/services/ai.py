import os

from groq import Groq

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
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return _fallback_synonyms(keyword)

    try:
        client = Groq(api_key=api_key, timeout=5.0)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un asistente que genera sinónimos y palabras relacionadas para monitorizar noticias en español. Responde SOLO con las palabras separadas por comas, sin explicaciones ni puntuación adicional.",
                },
                {
                    "role": "user",
                    "content": f"Dame entre 3 y 10 sinónimos o palabras relacionadas con '{keyword}' en español, útiles para monitorizar noticias.",
                },
            ],
            temperature=0.4,
            max_tokens=100,
        )
        raw = response.choices[0].message.content.strip()
        terms = [t.strip().lower() for t in raw.split(",") if t.strip()]
        base = keyword.lower().strip()
        seen: set[str] = set()
        result: list[str] = []
        for term in [base] + terms:
            if term and term not in seen:
                seen.add(term)
                result.append(term)
        return result[:11]
    except Exception:
        return _fallback_synonyms(keyword)
