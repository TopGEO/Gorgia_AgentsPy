import os
from dotenv import load_dotenv
from qdrant_client import AsyncQdrantClient
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
QDRANT_HOST = 'http://34.107.0.93:6333'
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
async_qdrant_client = AsyncQdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)

