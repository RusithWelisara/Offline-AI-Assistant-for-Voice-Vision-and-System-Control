import json
import logging
import asyncio
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class LLM:
    def __init__(self, model: str = "phi3-local", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self.api_url = f"{host}/api/generate"
        self.log_file = Path("logs/prompt_metrics.jsonl")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _log_metrics(self, prompt: str, system: str, response_data: dict, duration_ms: float):
        """Phase 1: Structured logging for regression baseline."""
        try:
            entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_ms": round(duration_ms, 2),
                "prompt_tokens": response_data.get("prompt_eval_count", 0),
                "response_tokens": response_data.get("eval_count", 0),
                "total_tokens": response_data.get("prompt_eval_count", 0) + response_data.get("eval_count", 0),
                "prompt_preview": (system + "\n" + prompt)[:200] + "...",
                "response_preview": str(response_data.get("response", ""))[:200] + "..."
            }
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")

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
            start_time = time.time()
            # Use asyncio.to_thread to make the blocking urlopen call async
            result = await asyncio.to_thread(self._make_request, payload)
            duration = time.time() - start_time
            logger.info(f"LLM Response Delay: {duration:.2f}s")
            return result

        except Exception as e:
            logger.error(f"LLM connection error: {e}")
            return self._error_response(str(e))

    async def chat_plain(self, prompt: str, system_prompt: Optional[str] = None, options: Optional[Dict] = None) -> str:
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
            "options": options or {}
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
                
                # Log token usage stats if available
                if "prompt_eval_count" in data:
                    logger.info(f"Token Usage - Prompt: {data.get('prompt_eval_count')} | Response: {data.get('eval_count')} | Total: {data.get('prompt_eval_count', 0) + data.get('eval_count', 0)}")
                
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


