from difflib import SequenceMatcher

def compute_text_similarity(query_text: str, reference_text: str) -> float:
    if not query_text or not reference_text:
        return 0.0
        
    return SequenceMatcher(None, query_text.lower(), reference_text.lower()).ratio()
