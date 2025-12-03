#!/bin/bash

# Esta línea hace que si cualquier comando falla, el script se detenga
set -e

echo "🚀 Iniciando contenedor con ROLE: $ROLE"

if [ "$ROLE" = "api" ]; then
    echo "🔵 Arrancando API (FastAPI)..."
    # Ejecutamos Uvicorn en el puerto 80 para que EasyPanel lo vea
    exec uvicorn app.main:app --host 0.0.0.0 --port 80

elif [ "$ROLE" = "worker" ]; then
    echo "🟢 Arrancando Worker (Celery)..."
    # Ejecutamos Celery (sin pool=solo porque en Linux/VPS no hace falta)
    exec celery -A worker_entry worker --loglevel=info

elif [ "$ROLE" = "frontend" ]; then
    echo "🟠 Arrancando Frontend (Streamlit)..."
    # Ejecutamos Streamlit en el puerto 8501
    exec streamlit run frontend/dashboard.py --server.port 8501 --server.address 0.0.0.0

else
    echo "🔴 ERROR: No has especificado la variable ROLE (api, worker, o frontend)"
    exit 1
fi