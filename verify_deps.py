try:
    import celery
    print(f"Celery version: {celery.__version__}")
    import redis
    print(f"Redis version: {redis.__version__}")
    from app.core.celery_app import celery_app
    print("Celery app imported successfully")
    import langfuse
    print(f"Langfuse version: {langfuse.__version__}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
