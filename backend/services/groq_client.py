"""
Groq LLM Client
backend/services/groq_client.py

Uses Groq's free API to run llama-3.3-70b-versatile.
14,400 requests/day free, ~500 tokens/sec inference.

Setup:
  1. Get free API key: https://console.groq.com/keys
  2. Add to backend/.env: GROQ_API_KEY=gsk_your_key_here
"""
import os
import json
import requests
from backend.utils import log


class GroqLLM:
    """Groq API client compatible with LangChain-style .invoke() and .stream()"""

    def __init__(self, model="llama-3.3-70b-versatile", temperature=0.3):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model = model
        self.temperature = temperature
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Get a free key at https://console.groq.com/keys "
                "and add it to your .env file."
            )

        log.info(f"✓ Groq LLM initialized (model: {self.model})")

    def _build_messages(self, prompt):
        """Convert a single prompt string into chat messages format."""
        return [{"role": "user", "content": prompt}]

    def invoke(self, prompt):
        """
        Generate a complete response (non-streaming).
        Compatible with LangChain's llm.invoke(prompt) interface.
        """
        payload = {
            "model": self.model,
            "messages": self._build_messages(prompt),
            "temperature": self.temperature,
            "max_tokens": 1024,
            "stream": False,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            resp = requests.post(self.base_url, json=payload, headers=headers, timeout=60)

            if resp.status_code == 429:
                log.warning("Groq rate limit hit, retrying in 2s...")
                import time
                time.sleep(2)
                resp = requests.post(self.base_url, json=payload, headers=headers, timeout=60)

            if resp.status_code != 200:
                log.error(f"Groq API error {resp.status_code}: {resp.text[:200]}")
                return f"Error: Groq API returned {resp.status_code}"

            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")

            return "No response generated."

        except requests.exceptions.Timeout:
            return "Error: Request timed out. Please try again."
        except Exception as e:
            log.error(f"Groq invoke error: {e}")
            return f"Error: {str(e)}"

    def stream(self, prompt):
        """
        Generate a streaming response (token by token).
        Compatible with LangChain's llm.stream(prompt) interface.
        Yields text chunks as they arrive.
        """
        payload = {
            "model": self.model,
            "messages": self._build_messages(prompt),
            "temperature": self.temperature,
            "max_tokens": 1024,
            "stream": True,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            resp = requests.post(self.base_url, json=payload, headers=headers, timeout=60, stream=True)

            if resp.status_code != 200:
                log.error(f"Groq stream error {resp.status_code}: {resp.text[:200]}")
                yield f"Error: Groq API returned {resp.status_code}"
                return

            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue

                json_str = line[6:]
                if json_str.strip() == "[DONE]":
                    break

                try:
                    data = json.loads(json_str)
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                except json.JSONDecodeError:
                    continue

        except requests.exceptions.Timeout:
            yield "Error: Request timed out."
        except Exception as e:
            log.error(f"Groq stream error: {e}")
            yield f"Error: {str(e)}"

    def __call__(self, prompt):
        """Allow calling as a function: llm(prompt)"""
        return self.invoke(prompt)