# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\llm_provider.py

import os
import requests
import json
from abc import ABC, abstractmethod
import google.generativeai as genai
import asyncio
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from google.api_core import exceptions # Import for API error handling

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
        model_name: str | None = None # Added for explicit model selection per call
    ) -> str:
        """Generates text based on a given prompt."""
        pass

# --- Gemini Implementation ---
class GeminiProvider(LLMProvider):
    """LLM Provider for Google's Gemini models with intelligent model selection."""

    def __init__(self, api_key: str | None = None, preferred_models: List[str] | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables or user profile.")
        
        genai.configure(api_key=self.api_key)
        # Default preferred models if none are provided, ordered by perceived free-tier limits
        self.preferred_models = preferred_models or [
            "gemini-2.0-flash",
            "gemini-2.5-flash-lite-preview-06-17",
            "gemma-3-and-3n",
            "gemini-1.5-flash" # Keep as a very last resort if explicitly requested or for compatibility
        ]

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 2048,
        model_name: str | None = None # Allows overriding the preferred list for a specific call
    ) -> str:
        # Determine which models to try for this specific call
        # If model_name is provided, try only that model first. Otherwise, use the preferred list.
        models_to_try = [model_name] if model_name else self.preferred_models

        last_exception = None
        for current_model in models_to_try:
            print(f"Attempting text generation with Gemini model: {current_model} (temp={temperature})...")
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            try:
                # Instantiate the model for each attempt to ensure correct model is used
                model = genai.GenerativeModel(current_model) 
                response = await model.generate_content_async(
                    prompt, generation_config=generation_config
                )
                if response.text:
                    return response.text
                else:
                    # Handle cases where response.text is empty but no error was raised
                    print(f"Warning: Gemini model {current_model} returned empty text for prompt. Trying next model if available.")
                    last_exception = Exception(f"Empty response from model {current_model}")
                    continue # Try next model
            except exceptions.ResourceExhausted as e:
                print(f"Quota exceeded for model {current_model}. Trying next model. Error: {e}")
                last_exception = e
                continue # Try the next model in the list
            except Exception as e:
                print(f"Error during Gemini text generation with {current_model}: {e}. Trying next model if available.")
                last_exception = e
                continue # Try the next model in the list
        
        # If the loop finishes without returning, all models failed
        if last_exception:
            print(f"All available Gemini models failed to generate text. Last error: {last_exception}")
            return f"# Error from Gemini: {last_exception}"
        else:
            # This case should ideally not be reached if models_to_try is not empty
            print("No Gemini models were attempted or no response was received.")
            return "# Error from Gemini: No models attempted or no response received."

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
        model_name: str | None = None # Ollama doesn't use this, but kept for interface consistency
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
        # Define the preferred order of Gemini models based on user's provided rate limits
        # Prioritize models with higher free tier RPD/RPM
        preferred_gemini_models = [
            "gemini-2.0-flash",
            "gemini-2.5-flash-lite-preview-06-17",
            "gemma-3-and-3n", # Lower token limits, but good as a last resort
            "gemini-1.5-flash" # The original model, kept as a last resort
        ]
        # Allow overriding the default list from config if provided
        models_to_use = config.get("models", preferred_gemini_models)
        return GeminiProvider(api_key=config.get("api_key"), preferred_models=models_to_use)
    elif provider_name == "ollama":
        return OllamaProvider(model_name=config.get("model", "llama3"), api_url=config.get("api_url"))
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
