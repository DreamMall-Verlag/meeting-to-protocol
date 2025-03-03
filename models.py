MODELS = {
    "bart-large-cnn": {
        "api": "huggingface",
        "model_id": "facebook/bart-large-cnn"
    },
    "gpt-4o": {
        "api": "openai",
        "model_id": "gpt-4o"
    },
    # Fügen Sie weitere Modelle nach Bedarf hinzu
}


PROMPT_TEMPLATE = '''
Fasse das folgende Meeting-Transkript in einem strukturierten Protokoll zusammen. Verwende dabei klare Überschriften und Aufzählungspunkte zur Strukturierung. 
erfasse alle:
- getroffenen aufgaben. 
- erfasse alle aufgetretenen problemen. 
- erfasse alle getroffenen entscheidungen. 
- erfasse alle getroffenen lösungen zu problemen.  
- erfasse alle termine. 
- erfasse alle anwesenden. 

Transkript:
{transcript}
'''
