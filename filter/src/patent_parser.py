import requests

def fetch_patent_description(doc_id: str) -> str:
    url = f"https://surechembl.org/api/document/{doc_id}/contents"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    # Navigate to descriptions
    try:
        descriptions = data['data']['contents']['patentDocument']['descriptions']
        # Find English description
        for desc in descriptions:
            if desc.get('lang') == 'EN' and 'section' in desc and 'content' in desc['section']:
                return desc['section']['content']
        return None
    except (KeyError, TypeError):
        return None