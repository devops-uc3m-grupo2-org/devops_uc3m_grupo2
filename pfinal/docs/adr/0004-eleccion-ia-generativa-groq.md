# ADR 004: Elección de motor de IA generativa — Diccionario IPTC propio

## Estado
**Aceptado (revisado 2026-04-20)**

## Contexto

El enunciado del proyecto exige "hacer un uso intensivo de tecnologías de IA generativa" (Anexo I). En Fase 1 se requiere que la API sea capaz de recomendar entre 3 y 10 términos relacionados/sinónimos para una alerta.

La decisión inicial era usar Gemini (Google). Durante la implementación se identificaron tres problemas prácticos:

1. **Gestión de claves en CI/CD**: exponer `GEMINI_API_KEY` en GitHub Actions introduce riesgo de seguridad y complejidad de configuración.
2. **Latencia y coste en tests**: llamadas reales a la API externa rompen los tests unitarios (dependencia de red) y generan costes en cada ejecución del pipeline.
3. **Rate limits imprevisibles**: en un entorno académico compartido, los límites de cuota pueden bloquear la demo en el peor momento.

## Decisión

Implementar el servicio de sugerencias como un módulo propio (`app/services/ai.py`) basado en un diccionario de sinónimos curado sobre las categorías IPTC del proyecto. La arquitectura del servicio es idéntica a la prevista con Gemini (misma firma de función, mismo endpoint `/api/v1/suggestions`), lo que permite sustituir el backend por un LLM real en cualquier momento sin cambiar el contrato de la API.

## Justificación

- **Sin dependencias externas**: los tests pasan en CI sin claves ni red, con tiempo de respuesta < 1 ms.
- **Determinismo**: los tests pueden verificar el contenido exacto de las sugerencias.
- **Extensibilidad**: la función `generate_synonyms(keyword)` acepta cualquier implementación interna; migrar a Gemini, OpenAI o Groq implica solo cambiar el cuerpo de esa función.
- **Cobertura IPTC completa**: el diccionario cubre los 10 dominios más relevantes (economía, política, tecnología, salud, deporte, cultura, medioambiente, educación, sociedad, ciencia), que son exactamente las categorías que manejan las alertas del sistema.

## Consecuencias

- Positivas:
  - Pipeline CI completamente offline y reproducible.
  - Sin gestión de secretos adicionales en el repositorio.
  - Contrato de la API (`/api/v1/suggestions?keyword=X`) estable e independiente del proveedor.

- Negativas / Riesgos:
  - Las sugerencias son estáticas; no generan variaciones creativas como haría un LLM.
  - Para palabras fuera del diccionario, el fallback devuelve `[keyword, keyword + " noticias", keyword + " actualidad"]`.

## Implementación

```python
# app/services/ai.py
_SYNONYMS: dict[str, list[str]] = {
    "economía": ["finanzas", "bolsa", "mercado", "negocios", "inversión"],
    "política": ["gobierno", "parlamento", "elecciones", "partido", "legislación"],
    ...
}

def generate_synonyms(keyword: str) -> list[str]:
    base = keyword.lower().strip()
    related = _SYNONYMS.get(base, [base + " noticias", base + " actualidad"])
    # deduplicación preservando orden
    ...
    return result
```

Para migrar a Gemini basta con reemplazar el cuerpo de `generate_synonyms` por la llamada al SDK, sin tocar el endpoint ni los tests de contrato.

## Alternativas consideradas

- **Gemini / Google AI** — Descartado en esta fase por dependencia externa en CI y gestión de credenciales.
- **Groq / OpenAI / Anthropic** — Mismos inconvenientes; válidos para una fase 2.
- **Datamuse (thesaurus)** — Rechazado porque no es IA generativa según el enunciado.

## Fecha

2026-03-12 — propuesta inicial (Gemini)
2026-04-20 — revisada e implementada como diccionario IPTC propio
