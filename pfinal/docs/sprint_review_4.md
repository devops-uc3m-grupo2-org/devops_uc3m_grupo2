# Sprint 4 – IA Generativa (Sinónimos y Clasificación)


En este sprint buscamos utilizar la Inteligencia Artificial Generativa para encontrar sinónimos de la palabra clave que el usuario ha elegido. En este caso, utilizamos Gemini (modelos generativos de Google) para completar la tarea.

---

## Objetivos de Sprint 4

- Utilizar la Inteligencia Artifical para generar sinónimos de la palabra.

- Exponer endpoints REST para:
  - Crear Sinonimos

---

Se ha coniderado el enfoque de llamadas HTTP al endpoint adecuado de Gemini o al API de Google Cloud (según el plan y la cuenta), configurando `GEMINI_API_URL` y `GEMINI_API_KEY` o las credenciales necesarias.

Sin embargo, ha dado problemas el uso de las credenciales, por este motivo también se ha considerado una opción utilizar la librería google.generativeai. 

*función ia sigue en proceso de desarrollo*
