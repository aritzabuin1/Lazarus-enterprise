# Base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m appuser

# Copy application code
COPY . .

# --- NUEVO: Damos permisos de ejecución al script ANTES de cambiar de usuario ---
RUN chmod +x start.sh

# 30. Change ownership to non-root user (ESTA LÍNEA YA LA TIENES)
RUN chown -R appuser:appuser /app

# 33. Switch to non-root user (ESTA LÍNEA YA LA TIENES)
USER appuser

# --- NUEVO: Definimos el script maestro como comando de arranque ---
CMD ["./start.sh"]