# core/llm_provider.py
import os
import requests
import json
from abc import ABC, abstractmethod
import google.generativeai as genai
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file in the project root
load_dotenv()

# --- Base Class ---
class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""
 
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 2048,
    ) -> str:
        """Generates text based on a given prompt."""
        pass

# --- Gemini Implementation ---
class GeminiProvider(LLMProvider):
    """LLM Provider for Google's Gemini models."""

    def __init__(self, api_key: str | None = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables or user profile.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 2048,
    ) -> str:
        print(f"Generating text with Gemini (temp={temperature})...")
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        try:
            response = await self.model.generate_content_async(
                prompt, generation_config=generation_config
            )
            return response.text
        except Exception as e:
            print(f"Error during Gemini text generation: {e}")
            return f"# Error from Gemini: {e}"

# --- Ollama Implementation ---
class OllamaProvider(LLMProvider):
    """LLM Provider for local Ollama models."""

    def __init__(self, model_name: str = "llama3", api_url: str = "http://localhost:11434/api/generate"):
        self.model_name = model_name
        self.api_url = api_url

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 2048,
    ) -> str:
        print(f"Generating text with Ollama model '{self.model_name}' (temp={temperature})...")
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "top_p": top_p}
        }

        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(self.api_url, json=payload, timeout=60))
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama: {e}")
            return f"# Error connecting to Ollama: {e}"

# --- Factory Function ---
def get_llm_provider(provider_name: str, config: dict) -> LLMProvider:
    """Factory function to get an instance of an LLM provider."""
    if provider_name == "gemini":
        return GeminiProvider(api_key=config.get("api_key"), model_name=config.get("model", "gemini-1.5-flash"))
    elif provider_name == "ollama":
        return OllamaProvider(model_name=config.get("model", "llama3"), api_url=config.get("api_url"))
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")