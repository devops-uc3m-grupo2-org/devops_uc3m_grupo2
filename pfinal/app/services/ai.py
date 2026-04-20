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


def generate_synonyms(keyword: str) -> list[str]:
    base = keyword.lower().strip()
    related = _SYNONYMS.get(base, [base + " noticias", base + " actualidad"])
    seen: set[str] = set()
    result: list[str] = []
    for term in [base] + related:
        if term not in seen:
            seen.add(term)
            result.append(term)
    return result
