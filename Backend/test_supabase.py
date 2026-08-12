import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")

print("URL loaded:", bool(url))
print("KEY loaded:", bool(key))
print("KEY prefix:", key[:15] if key else "EMPTY")

try:
    supabase = create_client(url, key)

    result = (
        supabase
        .table("organizations")
        .select("id, org_id, name")
        .limit(1)
        .execute()
    )

    print("SUCCESS!")
    print(result.data)

except Exception as e:
    print("SUPABASE ERROR:")
    print(type(e).__name__)
    print(str(e))