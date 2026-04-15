"""
Presidio Configuration - Use default spaCy model
"""
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

def create_secops_engines():
    """
    Create SecOps engines using default configuration
    """
    # Create analyzer with default settings (will use available spaCy model)
    analyzer = AnalyzerEngine()
    
    # Create anonymizer
    anonymizer = AnonymizerEngine()
    
    return analyzer, anonymizer
