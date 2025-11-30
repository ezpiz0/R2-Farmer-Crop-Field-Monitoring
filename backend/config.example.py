"""
Configuration Example for AgroSky Insight Backend
Copy this file to config.py and fill in your credentials
"""
import os

# Sentinel Hub credentials - Get them from https://apps.sentinel-hub.com/dashboard/
SENTINEL_CLIENT_ID = os.getenv("SENTINEL_CLIENT_ID", "your_sentinel_client_id_here")
SENTINEL_CLIENT_SECRET = os.getenv("SENTINEL_CLIENT_SECRET", "your_sentinel_secret_here")
SENTINEL_INSTANCE_ID = os.getenv("SENTINEL_INSTANCE_ID", "")  # Optional

# Gemini AI credentials - Get API key from https://ai.google.dev/
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key_here")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "generate_random_secret_key_min_32_chars")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

print("=" * 80)
print("🌍 AGROSKY INSIGHT - CONFIGURATION")
print("=" * 80)
print(f"⚠️  Using example configuration!")
print(f"📝 Copy this file to config.py and add your real credentials")
print("=" * 80)
