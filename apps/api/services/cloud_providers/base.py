"""Base classes for cloud caption providers"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class CloudCaptionResponse:
    """Response from cloud caption provider"""
    caption: str
    latency_ms: int
    cost_usd: float
    model: str
    input_tokens: int
    output_tokens: int
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "caption": self.caption,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


class CloudCaptionProvider(ABC):
    """Base class for cloud caption providers"""
    
    @abstractmethod
    async def caption(self, img_bytes: bytes) -> CloudCaptionResponse:
        """
        Generate caption for image using cloud API.
        
        Args:
            img_bytes: Raw image bytes (JPEG, PNG, etc.)
            
        Returns:
            CloudCaptionResponse with caption, latency, cost, and token usage
            
        Raises:
            Exception: If API call fails or image invalid
        """
        pass
    
    @abstractmethod
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost in USD for given token usage.
        
        Args:
            input_tokens: Number of input tokens (typically image encoding)
            output_tokens: Number of output tokens (caption text)
            
        Returns:
            Cost in USD (rounded to 6 decimal places)
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if provider is available and properly configured.
        
        Returns:
            True if provider can be used, False otherwise
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get human-readable provider name"""
        return self.__class__.__name__
