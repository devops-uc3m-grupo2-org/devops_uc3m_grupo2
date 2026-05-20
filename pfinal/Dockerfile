
FROM python:3.12-slim

# instalar dependencias del sistema necesarias para compilar bcrypt y otras extensiones
RUN apt-get update && \
	apt-get install -y --no-install-recommends \
		build-essential \
		gcc \
		python3-dev \
		libssl-dev \
		libffi-dev && \
	rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
