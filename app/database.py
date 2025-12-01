import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Warning: SUPABASE_URL or SUPABASE_KEY not found in environment variables.")
    # Create a dummy client or None to allow app to import without crashing
    # This is critical for running tests without real credentials
    class MockClient:
        def table(self, *args, **kwargs):
            return self
        def insert(self, *args, **kwargs):
            return self
        def execute(self, *args, **kwargs):
            return self
            
    supabase = MockClient()
else:
    supabase: Client = create_client(url, key)
