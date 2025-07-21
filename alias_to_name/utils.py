import json

import requests
import time

def fetch_patent(patent_number, retries=3, backoff=5):
    url = f"https://surechembl.org/api/document/{patent_number}/contents"
    headers = {"User-Agent": "Mozilla/5.0"}
    last_exception = None

    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=80)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            last_exception = e
            wait_time = backoff ** attempt
            print(f"Attempt {attempt+1} failed for {patent_number}: {e}. Retrying in {wait_time} sec...")
            time.sleep(wait_time)

    print(f"All attempts failed for {patent_number}.")
    raise last_exception


def split_text_with_overlap(text, chunk_size=1500, overlap=300):
    assert overlap < chunk_size, "Overlap must be smaller than chunk size"
    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += step

    return chunks

def get_alias_list(patent_data, measures):
    description = patent_data['data']['contents']['patentDocument']['descriptions'][0]['section']
    content = description['content']
    annotations = description['annotations']
    chemicals = []
    for a in annotations:
        if a['category'] == 'chemical' or a['category'] == 'target':
            chemicals.append(a['name'].lower().strip())

    aliases = set()
    for measure in measures:
        if isinstance(measure['molecule_name'], str):
            molecule_name = measure['molecule_name'].lower().strip()
            if molecule_name not in chemicals:
                aliases.add(measure['molecule_name'])
    return content, list(aliases)


def ask_llm(message, max_tokens=2000, temperature=0.3):
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


def process_patent(SYSTEM_PROMPT, USER_PROMPT, patent_number, measures):
    patent_data = fetch_patent(patent_number)
    content_for_patent, aliases_in_patent = get_alias_list(patent_data, measures)

    full_output = None
    for chunk_text in split_text_with_overlap(content_for_patent):
        # Filter aliases present in this chunk
        aliases_in_chunk = [alias for alias in aliases_in_patent if alias in chunk_text]
        if not aliases_in_chunk:
            continue
        user_prompt = USER_PROMPT.format(
            alias_list=", ".join(aliases_in_chunk),
            patent_text=chunk_text
        )
        message = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        output = ask_llm(message=message)
        full_output += output
        # # Extract JSON from model output (if not already JSON, parse as needed)
        # try:
        #     result_json = json.loads(output)
        # except Exception:
        #     # If model returns raw JSON lines or similar, parse accordingly
        #     # Optionally, you can use regex to extract JSONs from messy output
        #     continue
        #
        # results.append(result_json)
        # # Remove found aliases from pending_aliases
        # for entry in result_json:
        #     if entry.get('name') and entry.get('name') != "Not found":
        #         aliases_in_patent.remove(entry.get('name'))
        #
        # # Stop if all aliases are found
        # if not aliases_in_patent:
        #     break
    return full_output