from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine.spacy_nlp_engine import SpacyNlpEngine
from presidio_anonymizer import AnonymizerEngine

# Initialize Microsoft Presidio for local PII detection & anonymization
def create_secops_engines():
    # Use smaller spaCy model to save memory (en_core_web_sm ~12MB instead of en_core_web_lg ~400MB)
    nlp_engine = SpacyNlpEngine(models=[{"lang_code": "en", "model_name": "en_core_web_sm"}])
    
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
    
    anonymizer = AnonymizerEngine()
    
    return analyzer, anonymizer
