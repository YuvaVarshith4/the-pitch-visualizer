from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# Initialize Microsoft Presidio for local PII detection & anonymization
def create_secops_engines():
    analyzer = AnalyzerEngine()
    
    anonymizer = AnonymizerEngine()
    
    return analyzer, anonymizer
