"""Factory for creating cloud caption providers"""

import os
from typing import Optional
from .base import CloudCaptionProvider
from .mock import MockCloudProvider


class CloudProviderFactory:
    """
    Factory for creating cloud caption providers based on configuration.
    Supports OpenRouter, direct OpenAI/Gemini/Anthropic, and mock providers.
    """
    
    @staticmethod
    def create(provider_name: Optional[str] = None) -> CloudCaptionProvider:
        """
        Create a cloud caption provider based on configuration.
        
        Args:
            provider_name: Override provider name (default: from CLOUD_PROVIDER env)
            
        Returns:
            CloudCaptionProvider instance
            
        Raises:
            ValueError: If provider not supported or not configured
        """
        provider = provider_name or os.getenv("CLOUD_PROVIDER", "mock").lower()
        
        if provider == "mock":
            return MockCloudProvider()
        
        elif provider == "openrouter":
            try:
                from .openrouter import OpenRouterProvider
                return OpenRouterProvider()
            except ImportError as e:
                raise ValueError(f"OpenRouter provider not available: {e}")
            except Exception as e:
                print(f"[WARN] Failed to create OpenRouter provider: {e}")
                print("[WARN] Falling back to MockCloudProvider")
                return MockCloudProvider()
        
        elif provider == "openai":
            raise NotImplementedError("Direct OpenAI provider not yet implemented. Use 'openrouter' instead.")
        
        elif provider == "gemini":
            raise NotImplementedError("Direct Gemini provider not yet implemented. Use 'openrouter' instead.")
        
        elif provider == "anthropic":
            raise NotImplementedError("Direct Anthropic provider not yet implemented. Use 'openrouter' instead.")
        
        else:
            raise ValueError(f"Unknown cloud provider: {provider}")
    
    @staticmethod
    def list_providers() -> list[str]:
        """List available provider names"""
        return ["mock", "openrouter", "openai", "gemini", "anthropic"]
    
    @staticmethod
    def get_default_provider() -> str:
        """Get default provider from environment"""
        return os.getenv("CLOUD_PROVIDER", "mock").lower()
