"""OpenRouter cloud caption provider"""

import os
import time
import base64
import httpx
from typing import Optional
import yaml
from pathlib import Path

from .base import CloudCaptionProvider, CloudCaptionResponse
from .rate_limiter import get_rate_limiter


class OpenRouterProvider(CloudCaptionProvider):
    """
    OpenRouter vision API provider for image captioning.
    Supports multiple models through unified API.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize OpenRouter provider.
        
        Args:
            model: Model name (e.g., 'openai/gpt-4o-mini'). Defaults to env var.
            
        Raises:
            ValueError: If API key not configured
        """
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. Get one at https://openrouter.ai/"
            )
        
        self.model = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.rate_limiter = get_rate_limiter()
        
        # Load pricing configuration
        self._load_pricing()
        
        print(f"[OpenRouterProvider] Initialized with model: {self.model}")
        print(f"[OpenRouterProvider] Pricing: ${self.input_cost_per_million}/M input, ${self.output_cost_per_million}/M output")
    
    def _load_pricing(self):
        """Load pricing from YAML config"""
        pricing_path = Path(__file__).parent.parent.parent.parent / "costs" / "providers_openrouter.yaml"
        
        try:
            with open(pricing_path) as f:
                config = yaml.safe_load(f)
                models = config.get("models", {})
                model_config = models.get(self.model, {})
                
                self.input_cost_per_million = model_config.get("input_per_million", 0.15)
                self.output_cost_per_million = model_config.get("output_per_million", 0.60)
                
                if not model_config:
                    print(f"[WARN] Model {self.model} not in pricing config, using defaults")
        
        except Exception as e:
            print(f"[WARN] Could not load pricing config: {e}")
            # Defaults for gpt-4o-mini
            self.input_cost_per_million = 0.15
            self.output_cost_per_million = 0.60
    
    async def caption(self, img_bytes: bytes) -> CloudCaptionResponse:
        """
        Generate caption using OpenRouter vision API.
        
        Args:
            img_bytes: Raw image bytes (JPEG, PNG, etc.)
            
        Returns:
            CloudCaptionResponse with caption, latency, cost, and tokens
            
        Raises:
            Exception: If API call fails or rate limit exceeded
        """
        # Check rate limits
        estimated_cost = 0.001  # Rough estimate for rate limiter
        can_proceed, reason = self.rate_limiter.can_proceed(estimated_cost)
        if not can_proceed:
            raise Exception(f"Rate limit exceeded: {reason}")
        
        start = time.time()
        
        # Encode image to base64
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        # Detect image format (default to JPEG)
        img_format = self._detect_format(img_bytes)
        img_data_uri = f"data:image/{img_format};base64,{img_b64}"
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/ImageSearch",  # Optional: helps with rate limits
            "X-Title": "Image Search AI Router",  # Optional: for OpenRouter dashboard
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Generate a concise, descriptive caption for this image in one sentence. Focus on the main subject and key visual elements. Be specific and detailed."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": img_data_uri}
                        }
                    ]
                }
            ],
            "max_tokens": 100,
            "temperature": 0.7,
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
            
            latency_ms = int((time.time() - start) * 1000)
            
            # Parse response
            caption = data["choices"][0]["message"]["content"].strip()
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            
            # Calculate actual cost
            cost_usd = self.calculate_cost(input_tokens, output_tokens)
            
            # Record successful request with rate limiter
            self.rate_limiter.record_request(cost_usd)
            
            return CloudCaptionResponse(
                caption=caption,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            print(f"[ERROR] OpenRouter API error: {e.response.status_code} - {error_detail}")
            raise Exception(f"OpenRouter API error: {e.response.status_code}")
        
        except Exception as e:
            print(f"[ERROR] OpenRouter request failed: {e}")
            raise
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost in USD based on token usage.
        
        Args:
            input_tokens: Number of input tokens (includes image encoding)
            output_tokens: Number of output tokens (caption text)
            
        Returns:
            Cost in USD (rounded to 6 decimal places)
        """
        input_cost = (input_tokens / 1_000_000) * self.input_cost_per_million
        output_cost = (output_tokens / 1_000_000) * self.output_cost_per_million
        total_cost = input_cost + output_cost
        return round(total_cost, 6)
    
    def health_check(self) -> bool:
        """
        Check if OpenRouter provider is properly configured.
        
        Returns:
            True if API key is set, False otherwise
        """
        return bool(self.api_key)
    
    def _detect_format(self, img_bytes: bytes) -> str:
        """
        Detect image format from bytes.
        
        Args:
            img_bytes: Raw image bytes
            
        Returns:
            Format string ('jpeg', 'png', 'webp', etc.)
        """
        # Check magic bytes
        if img_bytes.startswith(b'\xff\xd8\xff'):
            return 'jpeg'
        elif img_bytes.startswith(b'\x89PNG'):
            return 'png'
        elif img_bytes.startswith(b'RIFF') and b'WEBP' in img_bytes[:12]:
            return 'webp'
        elif img_bytes.startswith(b'GIF'):
            return 'gif'
        else:
            # Default to jpeg
            return 'jpeg'
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return f"OpenRouter({self.model})"
    
    def get_rate_limiter_stats(self) -> dict:
        """Get rate limiter statistics"""
        return self.rate_limiter.get_stats()
