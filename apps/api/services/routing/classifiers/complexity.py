from dataclasses import dataclass
from typing import List, Set

@dataclass
class ComplexityScore:
    level: str  # "simple", "moderate", "complex"
    score: float  # 0.0 to 1.0 (1.0 = most complex)

class ComplexityClassifier:
    """
    Classifies query complexity to route appropriately.
    Simple: "red shoes" -> tag-based search / local models
    Complex: "melancholic cyberpunk atmosphere" -> LLM required
    """
    
    # Indicators of complex queries
    ABSTRACT_INDICATORS: Set[str] = {
        "atmosphere", "mood", "feeling", "reminiscent", 
        "style", "aesthetic", "vibe", "essence", "context",
        "emotional", "abstract", "surreal"
    }
    
    def classify(self, text: str) -> ComplexityScore:
        if not text:
            return ComplexityScore(level="simple", score=0.0)
            
        tokens = text.lower().split()
        
        # Count abstract vs concrete terms
        abstract_count = sum(1 for t in tokens if t in self.ABSTRACT_INDICATORS)
        
        # Heuristic for CAPTIONS (not just keywords)
        # 1. Very short captions are likely "Simple" (e.g. "a dog")
        if len(tokens) <= 5 and abstract_count == 0:
            return ComplexityScore(level="simple", score=0.2)
            
        # 2. Long, detailed captions OR abstract terms -> Complex
        # If it's long, it might be detailed enough that we don't need Cloud?
        # Actually, if Edge produces a LONG caption, it means it found a lot of stuff.
        # But usually Edge models are simple.
        # Let's stick to: Abstract terms = Complex.
        
        if abstract_count > 0:
            return ComplexityScore(level="complex", score=0.8)
            
        # 3. Moderate length without abstract terms -> Moderate
        return ComplexityScore(level="moderate", score=0.5)
