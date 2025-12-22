import json
import logging
import asyncio
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LLM:
    def __init__(self, model: str = "llama3.2:3b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self.api_url = f"{host}/api/generate"

    async def chat(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends a prompt to the LLM and returns specific structured JSON.
        Enforces use of llama3.2:3b for classification/suggestion.
        """
        full_system_prompt = (
            system_prompt or 
            "You are an autonomous planner. Respond ONLY in JSON."
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": full_system_prompt,
            "stream": False,
            "format": "json"
        }

        try:
            # Use asyncio.to_thread to make the blocking urlopen call async
            return await asyncio.to_thread(self._make_request, payload)

        except Exception as e:
            logger.error(f"LLM connection error: {e}")
            return self._error_response(str(e))

    async def chat_plain(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Sends a prompt to the LLM and returns plain text response.
        """
        full_system_prompt = (
            system_prompt or 
            "You are a helpful voice assistant. Keep your responses concise (1-2 sentences) and conversational."
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": full_system_prompt,
            "stream": False,
            # "format": "json" # Omitted for plain text
        }

        try:
            return await asyncio.to_thread(self._make_request, payload)
        except Exception as e:
            logger.error(f"LLM connection error: {e}")
            return f"Error: {e}"

    def _make_request(self, payload: Dict[str, Any]) -> Any:
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                self.api_url, 
                data=data, 
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                if response.status != 200:
                    logger.error(f"Ollama API error: {response.status}")
                    return self._error_response(f"API Error {response.status}")
                
                response_body = response.read().decode('utf-8')
                data = json.loads(response_body)
                response_text = data.get("response", "")
                
                # Check directly if format was requested as JSON in payload
                if payload.get("format") == "json":
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON response: {response_text}")
                        return self._error_response("Invalid JSON")
                
                return response_text

        except urllib.error.URLError as e:
            logger.error(f"Ollama connection error: {e}")
            if payload.get("format") == "json":
                 return self._error_response(str(e))
            return f"Error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            if payload.get("format") == "json":
                 return self._error_response(str(e))
            return f"Error: {str(e)}"

    def _error_response(self, reason: str) -> Dict[str, Any]:
        return {
            "intent": "error",
            "action": "wait",
            "reason": f"LLM Failure: {reason}"
        }

