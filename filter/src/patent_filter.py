import re

def patent_filter(patent: str) -> bool:
    if re.search(r'\b(IC50|Ki|EC50|Kd)\b', patent, re.IGNORECASE):
        return True
    return False