import json
import logging
import time
import asyncio
import google.generativeai as genai
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("gemini_client")

class GeminiError(Exception):
    pass

class GeminiClient:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. GeminiClient will fail.")
        else:
            genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Initialize models
        # Note: Using the exact model names provided in the prompt
        self.flash = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.pro = genai.GenerativeModel("gemini-1.5-pro")

    def _get_model(self, model_name: str):
        if model_name == "flash":
            return self.flash
        elif model_name == "pro":
            return self.pro
        else:
            # Default to pro if unknown, or raise error
            logger.warning(f"Unknown model '{model_name}', defaulting to 'pro'")
            return self.pro

    async def generate_json(self, prompt: str, model: str = "flash", max_retries: int = 3) -> dict:
        model_instance = self._get_model(model)
        full_prompt = prompt + "\n\nSystem Instruction: You are a JSON API. Respond with valid JSON only. No markdown, no code blocks, no explanation."
        
        start_time = time.time()
        attempt = 0
        backoff = 2
        
        while attempt < max_retries:
            try:
                # Use async generation
                response = await model_instance.generate_content_async(full_prompt)
                text = response.text
                
                # Clean up markdown code blocks if present
                clean_text = text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                elif clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                
                clean_text = clean_text.strip()
                
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
        model_instance = self._get_model(model)
        start_time = time.time()
        
        try:
            response = await model_instance.generate_content_async(prompt)
            latency = (time.time() - start_time) * 1000
            logger.info(f"Gemini Text success: model={model}, latency={latency:.2f}ms")
            return response.text
        except Exception as e:
            logger.error(f"Gemini Text failed: {e}")
            raise GeminiError(f"Failed to generate text: {e}")
