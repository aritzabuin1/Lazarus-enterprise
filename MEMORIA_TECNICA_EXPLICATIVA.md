# 📘 Memoria Técnica Explicativa: Lazarus Enterprise

> **Propósito de este documento**: Explicar el **QUÉ**, el **CÓMO** y, sobre todo, el **POR QUÉ** de cada decisión técnica tomada en este proyecto. Este documento está diseñado para que cualquier ingeniero entienda la profundidad de la arquitectura "Enterprise Grade".

---

## 1. Arquitectura del Sistema: Asincronía (Producer-Consumer)

### ¿Qué es?
En lugar de que el servidor web procese todo en el momento (sincrónico), delegamos las tareas pesadas a trabajadores en segundo plano.

### ¿Por qué lo usamos?
*   **El Problema**: Los LLMs (como GPT-4) son lentos. Generar una respuesta puede tardar 5-10 segundos. Si hacemos esto en el servidor web (`main.py`), el usuario ve un "cargando..." eterno y el servidor se bloquea si entran 100 usuarios a la vez.
*   **La Solución**:
    1.  El usuario envía un mensaje.
    2.  La API responde "Recibido" en 200ms (instantáneo).
    3.  La tarea se guarda en una cola (**Redis**).
    4.  Un proceso separado (**Celery Worker**) recoge la tarea y pasa 10 segundos pensando.
    5.  Cuando termina, notifica al usuario (vía WebSocket o Polling).

### Implementación
*   **Librería**: `Celery` (Gestor de tareas).
*   **Broker**: `Redis` (La cola donde se guardan los mensajes).

---

## 2. Redis: El Corazón de la Velocidad

### ¿Qué es?
Redis es una base de datos en memoria (RAM). A diferencia de Postgres (Disco Duro), Redis lee y escribe en microsegundos.

### ¿Para qué se usa en este proyecto?
Redis cumple **3 funciones críticas** aquí:

1.  **Message Broker (Cola de Tareas)**:
    *   Actúa como el intermediario entre la API y los Workers de Celery. Sin Redis, Celery no sabría qué tareas hay pendientes.
2.  **Rate Limiting (Control de Tráfico)**:
    *   *Problema*: ¿Cómo evitamos que un hacker tumbe el servidor con 1 millón de peticiones?
    *   *Solución*: Usamos `slowapi`. Necesitamos un lugar centralizado para contar cuántas veces ha llamado la IP `1.2.3.4` en el último minuto. Redis es perfecto para esto porque es rapidísimo incrementando contadores.
3.  **Semantic Caching (Caché de IA)**:
    *   Guardamos las respuestas de la IA para no repetir preguntas (ver sección 4).

---

## 3. Base de Datos: Supabase (PostgreSQL)

### ¿Qué es?
Supabase es una plataforma que nos da una base de datos PostgreSQL gestionada, con esteroides (Auth, Realtime, API).

### ¿Por qué PostgreSQL y no MongoDB?
*   **Integridad Relacional**: Nuestros datos tienen estructura clara (Usuarios -> Leads -> Mensajes). SQL es mejor para esto.
*   **Vector Support (`pgvector`)**: PostgreSQL permite guardar "embeddings" (vectores numéricos de texto) para hacer búsquedas semánticas (RAG) en el futuro. Es la base de datos estándar de la industria.

---

## 4. Semantic Caching (Optimización de IA)

### ¿Qué es?
Es una memoria inteligente. En lugar de buscar coincidencias exactas de texto (como una caché normal), busca coincidencias de **significado**.

### El Problema
*   Usuario A pregunta: *"¿Cuánto cuesta?"* -> OpenAI cobra $0.01 y tarda 3s.
*   Usuario B pregunta: *"¿Cuál es el precio?"* -> OpenAI cobra $0.01 y tarda 3s.
*   Para una caché normal, son textos distintos. Para OpenAI, es dinero tirado.

### La Solución (`GPTCache`)
1.  Convertimos la pregunta en un vector (números que representan significado).
2.  Si la pregunta del Usuario B se parece matemáticamente (distancia vectorial) a la del Usuario A, devolvemos la respuesta guardada.
3.  **Resultado**: Coste $0, Tiempo 0.05s.

---

## 5. Seguridad Cognitiva (AI Security)

### PII Redaction (Privacidad)
*   **Qué es**: "Personally Identifiable Information" (Información Personal Identificable).
*   **Por qué**: Enviar emails o teléfonos de clientes a OpenAI viola leyes como GDPR (Europa).
*   **Cómo**: Usamos **Microsoft Presidio**. Es un modelo de NLP local que escanea el texto, detecta entidades (PHONE, EMAIL) y las sustituye por `<PHONE>` antes de que el texto salga de nuestro servidor.

### Guardrails (Seguridad de Salida)
*   **Qué es**: Un filtro de seguridad para la IA.
*   **Por qué**: Los LLMs pueden "alucinar" o ser manipulados ("Prompt Injection") para decir cosas racistas, falsas o revelar secretos.
*   **Cómo**: Usamos **Guardrails AI**. Analiza la respuesta generada. Si detecta toxicidad o incumplimiento de reglas, bloquea la respuesta y devuelve un mensaje de error genérico.

---

## 6. Observabilidad: Ojos en el Sistema

### Sentry (Errores de Código)
*   Si el código falla (ej. división por cero, base de datos caída), Sentry nos avisa con la línea exacta del error y el estado de las variables. Sin esto, tendrías que adivinar mirando logs gigantes.

### LangFuse (Trazabilidad de IA)
*   **El Problema**: La IA es una "caja negra". No sabes por qué respondió lo que respondió.
*   **La Solución**: LangFuse graba cada interacción:
    *   Qué Prompt exacto se envió.
    *   Qué contexto se usó.
    *   Cuánto tardó.
    *   Cuánto costó (tokens).
*   Es vital para depurar "alucinaciones" y controlar el presupuesto.

---

## 7. Infraestructura como Código (IaC)

### Terraform
*   **Qué es**: Un lenguaje para definir infraestructura.
*   **Por qué**: Configurar servidores a mano (clic en AWS/Azure) es un error. Nadie recuerda qué botones tocó hace 6 meses.
*   **Cómo**: Definimos en un archivo `.tf`: "Quiero 1 servidor Ubuntu con 4GB RAM y Redis". Terraform se encarga de crearlo. Si se borra, ejecutamos el script y se recrea idéntico.

---

## 8. Docker & Multi-stage Builds

### ¿Qué es?
Empaquetamos la aplicación con todo lo que necesita para funcionar (librerías, sistema operativo base).

### Multi-stage (Optimización)
*   **Fase 1 (Builder)**: Usamos una imagen grande con compiladores (GCC) para instalar librerías pesadas.
*   **Fase 2 (Runner)**: Copiamos solo lo compilado a una imagen minúscula y limpia.
*   **Resultado**:
    *   Imagen más ligera (descarga rápido).
    *   Más segura (no tiene compiladores que un hacker podría usar).
    *   Sin usuario `root` (si entran, no tienen control total).

---

Este proyecto no es solo "código que funciona". Es un sistema diseñado para **escalar**, **protegerse** y **mantenerse** en el tiempo.
