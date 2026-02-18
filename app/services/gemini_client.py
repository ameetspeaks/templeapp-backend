import json
import logging
import time
import asyncio
import httpx
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("gemini_client")

class GeminiError(Exception):
    pass

class GeminiClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. GeminiClient will fail.")
        
        # Models configuration (REST API style)
        self.flash_model = "gemini-2.0-flash"
        self.pro_model = "gemini-1.5-pro"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def _get_model_name(self, model_alias: str) -> str:
        if model_alias == "flash":
            return self.flash_model
        elif model_alias == "pro":
            return self.pro_model
        else:
            return self.pro_model # Default

    async def _call_api(self, prompt: str, model_alias: str, is_json: bool = False) -> str:
        if not self.api_key:
            raise GeminiError("API Key missing")

        model_name = self._get_model_name(model_alias)
        url = f"{self.base_url}/{model_name}:generateContent?key={self.api_key}"
        
        headers = {"Content-Type": "application/json"}
        
        # Construct payload
        generation_config = {}
        if is_json:
            generation_config["response_mime_type"] = "application/json"
            
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": generation_config
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=60.0)
            
            if response.status_code != 200:
                logger.error(f"Gemini API Error {response.status_code}: {response.text}")
                raise GeminiError(f"API request failed: {response.status_code} - {response.text}")
                
            data = response.json()
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text
            except (KeyError, IndexError) as e:
                logger.error(f"Unexpected API response format: {data}")
                raise GeminiError(f"Failed to parse API response: {e}")

    async def generate_json(self, prompt: str, model: str = "flash", max_retries: int = 3) -> dict:
        full_prompt = prompt + "\n\nSystem Instruction: Respond with valid JSON only."
        start_time = time.time()
        attempt = 0
        backoff = 2
        
        while attempt < max_retries:
            try:
                text = await self._call_api(full_prompt, model, is_json=True)
                
                # Clean up potential markdown blocks if API returns them despite mime_type
                clean_text = text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                elif clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                
                result = json.loads(clean_text)
                
                latency = (time.time() - start_time) * 1000
                logger.info(f"Gemini JSON success: model={model}, latency={latency:.2f}ms")
                return result
                
            except Exception as e:
                attempt += 1
                logger.warning(f"Gemini JSON attempt {attempt} failed: {e}")
                if attempt >= max_retries:
                    logger.error(f"Gemini JSON failed after {max_retries} attempts")
                    raise GeminiError(f"Failed to generate JSON: {e}")
                
                await asyncio.sleep(backoff ** attempt)
        
        raise GeminiError("Max retries exhausted")

    async def generate_text(self, prompt: str, model: str = "pro") -> str:
        start_time = time.time()
        try:
            text = await self._call_api(prompt, model, is_json=False)
            latency = (time.time() - start_time) * 1000
            logger.info(f"Gemini Text success: model={model}, latency={latency:.2f}ms")
            return text
        except Exception as e:
            logger.error(f"Gemini Text failed: {e}")
            raise GeminiError(f"Failed to generate text: {e}")
