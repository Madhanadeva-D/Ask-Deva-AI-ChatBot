"""
model.py — Ask DeX API layer
Uses requests + json.dumps via OpenRouter.
API key is read fresh on every call, not cached at import time.
"""

import os
import json
import base64
from io import BytesIO

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _load_env():
    load_dotenv("env", override=True)


def _get_api_key() -> str:
    """Always reads the key fresh from disk — avoids stale cached values."""
    _load_env()
    return os.getenv("OPENROUTER_API_KEY", "").strip()


def get_api_key_display() -> str:
    """Convenience wrapper for display/checks in app.py — always fresh."""
    return _get_api_key()


_load_env()
SITE_URL  = os.getenv("YOUR_SITE_URL",  "http://localhost:8501")
SITE_NAME = os.getenv("YOUR_SITE_NAME", "Ask DeX")

MODEL   = "qwen/qwen3-vl-235b-a22b-thinking"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are Ask DeX, a powerful multimodal AI assistant built by Madhanadeva D.
If anyone asks who developed you or who created you, you must answer "Madhanadeva D.".
You can analyze images, charts, diagrams, screenshots, and documents.
Solve STEM and math problems with step-by-step reasoning.
Perform OCR and extract text from images. Convert UI screenshots to code.
Be accurate, helpful, and concise."""

# ---------------------------------------------------------------------------
# Request helpers
# ---------------------------------------------------------------------------

def get_headers() -> dict:
    """Always reads the key fresh — avoids stale cached value."""
    return {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": SITE_URL,
        "X-Title": SITE_NAME,
    }


def pil_to_base64_url(pil_image, fmt: str = "PNG") -> str:
    buf = BytesIO()
    pil_image.save(buf, format=fmt)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/{fmt.lower()};base64,{b64}"


def text_message(role: str, text: str) -> dict:
    return {"role": role, "content": [{"type": "text", "text": text}]}


def image_message(role: str, text: str, image_url: str) -> dict:
    return {
        "role": role,
        "content": [
            {"type": "text",      "text": text},
            {"type": "image_url", "image_url": {"url": image_url}},
        ],
    }

# ---------------------------------------------------------------------------
# API calls
# ---------------------------------------------------------------------------

def chat_stream(messages: list, max_tokens: int = 2048, temperature: float = 0.7):
    """
    Streaming generator — yields text chunks as they arrive.
    Raises Exception on API error so the caller can handle it gracefully.
    """
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True,
    }

    with requests.post(
        url=API_URL,
        headers=get_headers(),
        data=json.dumps(payload),
        stream=True,
        timeout=120,
    ) as response:

        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")

        for line in response.iter_lines():
            if not line:
                continue
            decoded = line.decode("utf-8").strip()
            if decoded.startswith("data: "):
                decoded = decoded[6:]
            if decoded == "[DONE]":
                break
            try:
                chunk = json.loads(decoded)
            except json.JSONDecodeError:
                continue
            choices = chunk.get("choices")
            if not choices:
                continue
            delta = choices[0].get("delta", {})
            content = delta.get("content") or ""
            if content:
                yield content