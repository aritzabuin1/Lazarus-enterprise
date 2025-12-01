import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.tasks.chat_tasks import process_chat
from app.core.celery_app import celery_app

client = TestClient(app)

# 1. TEST UNITARIO (El que tú hiciste, pulido)
# Verifica que la LÓGICA de la tarea funciona si le llegan datos
def test_unit_task_logic():
    print("\n🧪 [Unit] Probando lógica interna del Worker...")
    
    lead_context = {"id": "123", "name": "Test"}
    message = "Hola unitario"

    # Simulamos el agente para no gastar dinero ni tiempo
    with patch("app.tasks.chat_tasks.agent_app") as mock_agent:
        mock_agent.invoke.return_value = {"messages": [MagicMock(content="Respuesta Mock")]}
        
        # Ejecutamos la función DIRECTAMENTE (sin pasar por Redis)
        # .apply() ejecuta la tarea localmente y síncrona
        result = process_chat.apply(args=[message, lead_context]).get()
        
        assert result == "Respuesta Mock"
        print("✅ Lógica del worker correcta.")

# 2. TEST DE API (Endpoint)
# Verifica que la API usa .delay() y responde rápido
def test_api_queues_task():
    print("\n🧪 [API] Probando que el endpoint encola la tarea...")
    
    # Mockeamos la tarea de Celery para saber si la API la llamó
    with patch("app.tasks.chat_tasks.process_chat.delay") as mock_delay:
        # Simulamos que .delay devuelve un objeto con id
        mock_task = MagicMock()
        mock_task.id = "task-uuid-123"
        mock_delay.return_value = mock_task

        # Hacemos la petición real a la API
        response = client.post("/chat", json={"message": "Hola", "lead_id": "123"})
        
        # Verificaciones
        assert response.status_code == 202
        data = response.json()
        assert data["task_id"] == "task-uuid-123"
        assert data["status"] == "queued"
        
        # ¿Se llamó a .delay?
        mock_delay.assert_called_once()
        print("✅ La API encola correctamente (usa .delay).")

# 3. TEST DE INTEGRACIÓN (Redis Real)
# Verifica que Celery se puede conectar a Redis (requiere Docker levantado)
def test_integration_redis_connection():
    print("\n🧪 [Infra] Probando conexión real con Redis...")
    try:
        with celery_app.connection() as connection:
            connection.ensure_connection(max_retries=3)
            print("✅ Conexión con Redis exitosa.")
    except Exception as e:
        pytest.fail(f"❌ FALLO CRÍTICO: Celery no ve a Redis. ¿Está Docker encendido? Error: {e}")