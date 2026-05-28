import asyncio
import httpx
import os

WHISPER_BASE_URL = os.getenv("WHISPER_BASE_URL", "http://whisper-worker:8000")

async def test():
    print(f"Testing connection to: {WHISPER_BASE_URL}")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{WHISPER_BASE_URL}/health")
            print(f"✅ Success! Status: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
