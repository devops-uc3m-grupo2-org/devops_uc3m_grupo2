# ADR 004: Elección de motor de IA generativa — Gemini

## Estado
**Aceptado**

## Contexto

El enunciado del proyecto exige "hacer un uso intensivo de tecnologías de IA generativa" (Anexo I). En Fase 1 se requiere que la API sea capaz de recomendar entre 3 y 10 términos relacionados/sinónimos para una alerta. APIs tipo thesaurus (p.ej. Datamuse) no encajan con la definición de "IA generativa" exigida por el profesorado.

Requisitos clave:

- Respuestas generativas controladas por prompt (no solo lookup/thesaurus)
- Latencia/velocidad suficiente para el uso en endpoints sin bloquear la experiencia
- Facilidad de integración mediante HTTP y control de prompt
- Plan de contingencia si la API falla o alcanza límites

## Decisión

Usar Gemini (modelos generativos de Google) como proveedor principal de IA generativa para la funcionalidad de sugerencias en Fase 1. La integración se hará mediante llamadas HTTP al endpoint adecuado de Gemini o al API de Google Cloud (según el plan y la cuenta), configurando `GEMINI_API_URL` y `GEMINI_API_KEY` o las credenciales necesarias.

## Justificación

- Gemini es un LLM de propósito general con capacidades generativas que encajan con el requisito del proyecto.
- Permite prompt engineering y obtener respuestas en texto o en formatos estructurados (JSON) según el prompt.
- Amplio soporte, latencia competitiva y ecosistema de Google Cloud para escalado futuro.
- Integración posible mediante llamadas HTTP directas o con SDKs oficiales (si se decide usar cliente).

## Consecuencias

- Positivas:
  - Cumple explícitamente el requisito de IA generativa del proyecto.
  - Calidad de las sugerencias superior a un thesaurus, mayor flexibilidad en prompt.

- Negativas / Riesgos:
  - Dependencia de un proveedor externo y gestión de claves/credenciales; requiere control de costes y límites.
  - Puede requerir adaptación del prompt y post-procesado para garantizar salida JSON válida.

## Implementación (resumen)

- Endpoint en `app/services/ia.py` que llama a `GEMINI_API_URL` con `GEMINI_API_KEY` o usa cliente oficial.
- Prompt que solicita explícitamente JSON del tipo { "terms": ["t1","t2",...] } y lógica de fallback para parseo robusto.
- Documentar variables de entorno en README y `.env.example` (p.ej. `GEMINI_API_URL`, `GEMINI_API_KEY`, o `GOOGLE_APPLICATION_CREDENTIALS` si se usa autenticación por archivo de credenciales).

## Alternativas consideradas

- Datamuse / thesaurus — Rechazado (no IA generativa).
- Groq, OpenAI, Anthropic — válidos; Gemini elegido por alineación con requisitos de calidad y ecosistema del equipo (puede reevaluarse según costes y disponibilidad).

## Mitigaciones y fallback

- Implementar caché de resultados y límites de tasa para evitar costes excesivos.
- Proveer fallback a una solución de thesaurus simple si la API de Gemini falla o no responde en producción.

## Fecha

2026-03-12 — propuesta por el equipo de desarrollo
