import pytest
from apps.api.services.routing.classifiers.complexity import ComplexityClassifier

def test_complexity_classifier_simple():
    classifier = ComplexityClassifier()
    # Simple query
    score = classifier.classify("red shoes")
    assert score.level == "simple"
    assert score.score < 0.3

def test_complexity_classifier_complex():
    classifier = ComplexityClassifier()
    # Complex query with abstract terms
    score = classifier.classify("a melancholic cyberpunk atmosphere with neon lights")
    assert score.level == "complex"
    assert score.score > 0.7

def test_complexity_classifier_moderate():
    classifier = ComplexityClassifier()
    # Moderate query
    score = classifier.classify("a dog running in the park")
    assert score.level == "moderate"
    assert score.score >= 0.3
    assert score.score <= 0.7

def test_complexity_classifier_empty():
    classifier = ComplexityClassifier()
    score = classifier.classify("")
    assert score.level == "simple"
    assert score.score == 0.0
