import requests
import time

def fetch_patent(patent_number, retries=3, backoff=5):
    url = f"https://surechembl.org/api/document/{patent_number}/contents"
    headers = {"User-Agent": "Mozilla/5.0"}
    last_exception = None

    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            last_exception = e
            wait_time = backoff ** attempt
            print(f"Attempt {attempt+1} failed for {patent_number}: {e}. Retrying in {wait_time} sec...")
            time.sleep(wait_time)

    print(f"All attempts failed for {patent_number}.")
    raise last_exception


def split_text_with_overlap(text, chunk_size=2000, overlap=500):
    assert overlap < chunk_size, "Overlap must be smaller than chunk size"
    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += step

    return chunks


def ask_llm(message, max_tokens=100, temperature=0.8):
    from openai import OpenAI

    client = OpenAI(
        base_url="http://80.209.242.40:8000/v1",
        api_key="dummy-key"
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-instruct",
        messages=message,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content