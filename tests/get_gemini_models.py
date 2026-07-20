from google import genai
from google.genai import types


GEMINI_API_KEY = ""

client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(
        timeout=90000,
        retry_options=types.HttpRetryOptions(attempts=2),
    ),
)

for m in client.models.list():
    print(m.name, "->", m.supported_actions)