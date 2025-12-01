"""
Test de conexión a Redis (Upstash)
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

print("=" * 60)
print("VERIFICANDO CONEXIÓN A REDIS (UPSTASH)")
print("=" * 60)

# 1. Verificar que la configuración se carga correctamente
print("\n[1/3] Verificando configuración...")
try:
    from app.core.config import settings
    print(f"✅ REDIS_URL cargado desde .env")
    # Mostrar solo el host para seguridad
    if "upstash.io" in settings.REDIS_URL:
        print(f"   Host: Upstash (conexión segura)")
    else:
        print(f"   Host: {settings.REDIS_URL.split('@')[1] if '@' in settings.REDIS_URL else 'localhost'}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# 2. Verificar que Celery puede usar la configuración
print("\n[2/3] Verificando Celery...")
try:
    from app.core.celery_app import celery_app
    print(f"✅ Celery app inicializado")
    print(f"   Broker: {'Upstash' if 'upstash' in celery_app.conf.broker_url else 'Local'}")
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# 3. Intentar conexión real a Redis
print("\n[3/3] Probando conexión real a Redis...")
try:
    with celery_app.connection() as connection:
        connection.ensure_connection(max_retries=3, timeout=5)
        print("✅ Conexión a Redis exitosa!")
        print("   Estado: CONECTADO")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    print("   Verifica que la URL de Upstash sea correcta")
    sys.exit(1)

print("\n" + "=" * 60)
print("REDIS CONFIGURADO CORRECTAMENTE ✨")
print("Ahora puedes ejecutar:")
print("  celery -A worker_entry worker --loglevel=info")
print("=" * 60)
