import openai
import json
import time
import logging
import re
import os
from tqdm import tqdm

from . import config

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _extract_json_from_response(response_text: str) -> str | None:
    """Extracts a JSON string from a markdown code block or the raw text."""
    # First, try to find a JSON block marked with ```json
    match = re.search(r"```json\s*([\s\S]*?)\s*```", response_text)
    if match:
        return match.group(1).strip()
    
    # If no markdown block is found, try to find the first occurrence of a valid JSON object or list
    # This is a fallback for when the LLM doesn't use markdown
    match = re.search(r"(\[[\s\S]*\]|{[\s\S]*})", response_text)
    if match:
        return match.group(0).strip()
        
    logging.warning("Could not find a JSON block in the response.")
    return None

# --- LLM Call Function ---
def _call_llm(prompt: str) -> str | None:
    """
    Calls the LLM API with retry logic.
    """
    for attempt in range(config.API_RETRY_ATTEMPTS):
        try:
            client = openai.OpenAI(api_key=config.API_KEY, base_url=config.API_BASE_URL)
            response = client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.TEMPERATURE,
                max_tokens=config.MAX_TOKENS_RESPONSE,
            )
            # Correctly access the content from the response object
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content
            else:
                logging.error("Invalid response structure from API.")
                return None
        except Exception as e:
            logging.error(f"API call failed on attempt {attempt + 1}: {e}")
            if attempt < config.API_RETRY_ATTEMPTS - 1:
                time.sleep(config.API_RETRY_DELAY)
            else:
                logging.error("All API retry attempts failed.")
                return None

# --- Chunking Function ---
def _get_relevant_chunks(text: str) -> list[str]:
    """
    Finds relevant chunks of text based on metric keywords and filters out negative keywords.
    """
    # 1. Find all metric positions
    metric_positions = [m.start() for m in re.finditer(config.METRIC_REGEX_PATTERN, text, re.IGNORECASE)]
    if not metric_positions:
        return []

    # 2. Create intervals
    intervals = []
    for pos in metric_positions:
        start = max(0, pos - config.CHUNK_CONTEXT_SIZE)
        end = min(len(text), pos + config.CHUNK_CONTEXT_SIZE)
        intervals.append((start, end))

    # 3. Merge overlapping intervals
    if not intervals:
        return []
        
    intervals.sort(key=lambda x: x[0])
    merged_intervals = [intervals[0]]
    for current_start, current_end in intervals[1:]:
        last_start, last_end = merged_intervals[-1]
        if current_start < last_end:
            merged_intervals[-1] = (last_start, max(last_end, current_end))
        else:
            merged_intervals.append((current_start, current_end))

    # 4. Extract text and 5. Apply negative filter
    final_chunks = []
    for start, end in merged_intervals:
        chunk = text[start:end]
        if not re.search(config.NEGATIVE_KEYWORDS_REGEX, chunk, re.IGNORECASE):
            final_chunks.append(chunk)

    return final_chunks

# --- Extractor Agent ---
class _ExtractorAgent:
    """
    An agent that extracts structured data from a text chunk using a two-step LLM process.
    """
    def run(self, text_chunk: str, patent_id: str, debug: bool = False, debug_output_dir: str | None = None) -> tuple[str | None, list[dict]]:
        """
        Runs the two-step extraction process.
        Returns the raw mentions and the extracted data.
        """
        if debug and debug_output_dir is None:
            debug_output_dir = config.DEBUG_OUTPUT_DIR

        # Step 1: Find raw mentions
        find_prompt = config.EXTRACTOR_FIND_PROMPT.format(text_chunk=text_chunk)
        raw_mentions = _call_llm(find_prompt)

        if not raw_mentions or "no relevant" in raw_mentions.lower():
            logging.info("No raw mentions found by the extractor agent.")
            return None, []

        # Debugging: Save raw mentions
        if debug:
            debug_dir = os.path.join(debug_output_dir, patent_id)
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, "02_extractor_outputs.jsonl"), "a") as f:
                f.write(json.dumps({"raw_mentions": raw_mentions}) + "\n")

        # Step 2: Format into JSON
        format_prompt = config.EXTRACTOR_FORMAT_PROMPT.format(raw_mentions=raw_mentions)
        json_response = _call_llm(format_prompt)

        if not json_response:
            logging.error("Failed to get a formatted JSON response from the LLM.")
            return raw_mentions, []

        # JSON Self-Correction
        extracted_data = []
        try:
            json_to_parse = _extract_json_from_response(json_response)
            if not json_to_parse:
                raise json.JSONDecodeError("No JSON found in the LLM response", json_response, 0)
            extracted_data = json.loads(json_to_parse)
        except json.JSONDecodeError:
            logging.warning(f"Initial JSON parsing failed. Raw response:\n{json_response}\nAttempting self-correction.")
            correction_prompt = config.JSON_CORRECTION_PROMPT.format(invalid_json_text=json_response)
            corrected_json_response = _call_llm(correction_prompt)
            if not corrected_json_response:
                logging.error("LLM failed to provide a corrected JSON.")
                return raw_mentions, []
            try:
                json_to_parse = _extract_json_from_response(corrected_json_response)
                if not json_to_parse:
                    raise json.JSONDecodeError("No JSON found in the corrected LLM response", corrected_json_response, 0)
                extracted_data = json.loads(json_to_parse)
                json_response = corrected_json_response # Use corrected version for debug log
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON even after correction: {e}")
                logging.error(f"Original response: {json_response}")
                logging.error(f"Corrected response: {corrected_json_response}")
                return raw_mentions, []
        
        # Debugging: Save final JSON
        if debug and extracted_data:
            debug_dir = os.path.join(debug_output_dir, patent_id)
            with open(os.path.join(debug_dir, "02_extractor_outputs.jsonl"), "a") as f:
                f.write(json.dumps({"final_json": extracted_data}) + "\n")

        return raw_mentions, extracted_data


# --- Main Processing Function ---
def process_patent_text(patent_text: str, associated_molecules: list[dict], patent_id: str, debug: bool = False, debug_output_dir: str | None = None) -> list[dict]:
    """
    Processes the full text of a patent to extract bioactivity data.
    """
    # Determine debug directory
    if debug and debug_output_dir is None:
        debug_output_dir = config.DEBUG_OUTPUT_DIR

    # 1. Get relevant chunks
    relevant_chunks = _get_relevant_chunks(patent_text)
    logging.info(f"Found {len(relevant_chunks)} relevant chunks for patent {patent_id}.")

    # 2. Debug: Save chunks
    if debug:
        debug_dir = os.path.join(debug_output_dir, patent_id)
        os.makedirs(debug_dir, exist_ok=True)
        with open(os.path.join(debug_dir, "01_chunks.json"), "w") as f:
            json.dump(relevant_chunks, f, indent=4)
        
        # Clear previous extractor outputs for this patent
        extractor_output_file = os.path.join(debug_dir, "02_extractor_outputs.jsonl")
        if os.path.exists(extractor_output_file):
            os.remove(extractor_output_file)


    # 3. Create agent instance
    agent = _ExtractorAgent()

    # 4. & 5. Loop through chunks and extract data
    all_extracted_data = []
    for chunk in tqdm(relevant_chunks, desc=f"Processing chunks for {patent_id}"):
        raw_mentions, extracted_data = agent.run(chunk, patent_id, debug, debug_output_dir)
        if extracted_data:
            # Post-filter the results to ensure they meet the criteria
            for item in extracted_data:
                if item.get("value") and item.get("unit") and item.get("molecule_name") and item.get("binding_metric"):
                    item["raw_mentions"] = raw_mentions  # Add the source mentions for debugging
                    all_extracted_data.append(item)

    logging.info(f"Extracted {len(all_extracted_data)} data points from patent {patent_id}.")
    
    # 6. Return all data
    return all_extracted_data
