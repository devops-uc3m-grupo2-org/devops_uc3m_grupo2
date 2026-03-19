# Práctica 6 — API REST (FastAPI)

Instrucciones rápidas:

1. Crear y activar entorno virtual:

```bash
python -m venv venv
\# Windows
.\venv\Scripts\activate
\# Mac/Linux
source venv/bin/activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

3. Ejecutar servidor:

```bash
uvicorn main:app --reload
```

4. Abrir Swagger UI: http://127.0.0.1:8000/docs

Archivos principales:

- `main.py`: endpoints REST (POST/GET/PUT/DELETE)
- `models.py`: modelo `Ticket` (Pydantic)
- `repository.py`: almacenamiento en memoria
- `service.py`: reglas de negocio
