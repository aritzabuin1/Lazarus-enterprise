# disparo_manual.py
import sys
import os

# Añadimos el directorio actual al path para encontrar los módulos
sys.path.append(os.getcwd())

from app.tasks.chat_tasks import process_chat

print("🚀 Enviando tarea a la nube (Redis)...")

# USAMOS .delay() -> Esto envía el mensaje a Redis, no ejecuta la función localmente
task = process_chat.delay(
    message="Hola, probando la arquitectura asíncrona",
    lead_context={"id": "test-manual", "name": "Arquitecto Aritz"}
)

print(f"✅ Tarea enviada! El Ticket ID es: {task.id}")
print("👉 AHORA MIRA LA OTRA TERMINAL (La del Worker)")