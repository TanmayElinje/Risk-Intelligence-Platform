"""
Gemini LLM Client
backend/services/gemini_client.py

Drop-in replacement for Ollama LLM. Uses Google Gemini API (free tier).
Supports both regular and streaming generation.

Setup:
  1. Get free API key: https://aistudio.google.com/apikey
  2. Add to backend/.env: GEMINI_API_KEY=your_key_here
"""
import os
import json
import requests
from backend.utils import log


class GeminiLLM:
    """Google Gemini API client compatible with LangChain-style .invoke() and .stream()"""

    def __init__(self, model="gemini-2.0-flash", temperature=0.3):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model = model
        self.temperature = temperature
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Get a free key at https://aistudio.google.com/apikey "
                "and add it to your .env file."
            )

        log.info(f"✓ Gemini LLM initialized (model: {self.model})")

    def invoke(self, prompt):
        """
        Generate a complete response (non-streaming).
        Compatible with LangChain's llm.invoke(prompt) interface.
        """
        url = f"{self.base_url}/models/{self.model}:generateContent"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": 1024,
            },
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)

            if resp.status_code == 429:
                log.warning("Gemini rate limit hit, retrying in 2s...")
                import time
                time.sleep(2)
                resp = requests.post(url, json=payload, headers=headers, timeout=60)

            if resp.status_code != 200:
                log.error(f"Gemini API error {resp.status_code}: {resp.text[:200]}")
                return f"Error: Gemini API returned {resp.status_code}"

            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")

            return "No response generated."

        except requests.exceptions.Timeout:
            return "Error: Request timed out. Please try again."
        except Exception as e:
            log.error(f"Gemini invoke error: {e}")
            return f"Error: {str(e)}"

    def stream(self, prompt):
        """
        Generate a streaming response (token by token).
        Compatible with LangChain's llm.stream(prompt) interface.
        Yields text chunks as they arrive.
        """
        url = f"{self.base_url}/models/{self.model}:streamGenerateContent?alt=sse"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": 1024,
            },
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60, stream=True)

            if resp.status_code != 200:
                log.error(f"Gemini stream error {resp.status_code}: {resp.text[:200]}")
                yield f"Error: Gemini API returned {resp.status_code}"
                return

            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue

                json_str = line[6:]  # Remove "data: " prefix
                if json_str.strip() == "[DONE]":
                    break

                try:
                    data = json.loads(json_str)
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            text = parts[0].get("text", "")
                            if text:
                                yield text
                except json.JSONDecodeError:
                    continue

        except requests.exceptions.Timeout:
            yield "Error: Request timed out."
        except Exception as e:
            log.error(f"Gemini stream error: {e}")
            yield f"Error: {str(e)}"

    def __call__(self, prompt):
        """Allow calling as a function: llm(prompt)"""
        return self.invoke(prompt)