# ADR 004: Elección de motor de IA generativa — Groq (Llama 3.3 70B)

## Estado
**Aceptado (revisado 2026-05-11)**

## Contexto

El enunciado del proyecto exige "hacer un uso intensivo de tecnologías de IA generativa" (Anexo I). En Fase 1 se requiere que la API sea capaz de recomendar entre 3 y 10 términos relacionados/sinónimos para una alerta.

La decisión inicial era usar Gemini (Google). Durante la implementación se identificaron problemas prácticos:

1. **Quota 0 en free tier**: el proyecto académico de Google Cloud tiene `limit: 0` para todos los modelos de Gemini, lo que impide cualquier llamada desde el entorno universitario.
2. **Restricciones regionales**: las cuentas de educación de la UC3M tienen limitaciones adicionales en Google AI Studio.

## Decisión

Usar **Groq** con el modelo `llama-3.3-70b-versatile` como proveedor de IA generativa, con fallback a un diccionario IPTC propio si la API no está disponible. La clave se configura mediante `GROQ_API_KEY` en `.env`.

## Justificación

- **Free tier real**: Groq ofrece miles de tokens gratuitos al día sin restricciones académicas.
- **Velocidad**: Groq es uno de los proveedores de inferencia más rápidos disponibles.
- **Llama 3.3 70B**: modelo open source de Meta con excelente calidad para tareas en español.
- **Fallback robusto**: si `GROQ_API_KEY` no está configurada o la API falla, el sistema usa el diccionario IPTC sin interrumpir el servicio.
- **CI sin dependencias externas**: en CI no se configura `GROQ_API_KEY`, por lo que los tests usan el fallback y pasan sin red ni secretos.

## Consecuencias

- Positivas:
  - Cumple el requisito de IA generativa con LLM real en producción.
  - Sugerencias dinámicas y contextualmente relevantes para cualquier keyword.
  - Sin coste en CI; sin riesgo de romper el pipeline por rate limits.

- Negativas / Riesgos:
  - Dependencia de Groq como proveedor externo en producción.
  - La clave `GROQ_API_KEY` debe configurarse en `.env` para activar Groq; sin ella se usa el diccionario.

## Implementación

```python
# app/services/ai.py
def generate_synonyms(keyword: str) -> list[str]:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return _fallback_synonyms(keyword)  # diccionario IPTC
    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", ...
        )
        ...
    except Exception:
        return _fallback_synonyms(keyword)
```

## Alternativas consideradas

- **Gemini / Google AI** — Descartado por quota 0 en el proyecto académico de la UC3M.
- **OpenAI / Anthropic** — Requieren tarjeta de crédito para free tier.
- **Datamuse (thesaurus)** — Rechazado porque no es IA generativa según el enunciado.
- **Diccionario IPTC puro** — Usado como fallback; insuficiente como solución principal.

## Fecha

2026-03-12 — propuesta inicial (Gemini)
2026-04-20 — revisada como diccionario IPTC propio
2026-05-11 — implementada con Groq + fallback al diccionario
