"""
Test End-to-End del flujo asíncrono
Simula una petición real al endpoint /chat
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("TEST END-TO-END: FLUJO ASÍNCRONO COMPLETO")
print("=" * 70)

# 1. Enviar mensaje al endpoint /chat
print("\n[1/3] Enviando mensaje al endpoint /chat...")
try:
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": "Hola, me interesa el servicio",
            "lead_id": "test-lead-123"
        }
    )
    
    if response.status_code == 202:
        data = response.json()
        task_id = data["task_id"]
        print(f"✅ Mensaje encolado exitosamente")
        print(f"   Task ID: {task_id}")
        print(f"   Status: {data['status']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
        
except requests.exceptions.ConnectionError:
    print("❌ Error: No se puede conectar al servidor")
    print("   Asegúrate de que el servidor FastAPI esté corriendo:")
    print("   uvicorn app.main:app --reload")
    exit(1)

# 2. Polling del estado de la tarea
print(f"\n[2/3] Haciendo polling del estado (task_id: {task_id})...")
max_attempts = 30
attempt = 0

while attempt < max_attempts:
    attempt += 1
    time.sleep(2)  # Esperar 2 segundos entre intentos
    
    try:
        response = requests.get(f"{BASE_URL}/tasks/{task_id}")
        data = response.json()
        status = data["status"]
        
        print(f"   Intento {attempt}: {status}")
        
        if status == "completed":
            print(f"\n✅ Tarea completada!")
            print(f"   Respuesta del agente:")
            print(f"   {data['result'][:200]}...")
            break
        elif status == "failed":
            print(f"\n❌ Tarea falló")
            print(f"   Error: {data.get('error', 'Unknown')}")
            break
        elif status == "processing":
            print(f"   ⏳ Procesando... (esperando)")
            
    except Exception as e:
        print(f"   ❌ Error consultando estado: {e}")
        break
else:
    print(f"\n⚠️  Timeout: La tarea no completó en {max_attempts * 2} segundos")

print("\n" + "=" * 70)
print("TEST COMPLETADO")
print("=" * 70)
