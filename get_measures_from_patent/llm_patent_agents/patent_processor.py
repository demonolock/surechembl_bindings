import json
import logging
import os
from tqdm import tqdm

from common_utils.call_llm import LLM
from common_utils.get_relevants_chunks import get_relevant_chunks
from get_measures_from_patent.config import ConfigLLM
from .extractor_agent import ExtractorAgent

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Main Processing Function ---
def process_patent_text(patent_text: str, associated_molecules: list[dict], patent_id: str, config: ConfigLLM,
                        debug: bool = False, debug_output_dir: str | None = None) -> list[dict]:
    """
    Processes the full text of a patent to extract bioactivity data.
    """
    # Determine debug directory
    if debug and debug_output_dir is None:
        debug_output_dir = config.DEBUG_OUTPUT_DIR

    # 1. Get relevant chunks
    relevant_chunks = get_relevant_chunks(
        patent_text,
        config.METRIC_REGEX_PATTERN,
        config.CHUNK_CONTEXT_SIZE,
        config.NEGATIVE_KEYWORDS_REGEX
    )
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
    llm = LLM(config.API_RETRY_ATTEMPTS, config.API_KEY, config.API_BASE_URL, config.TEMPERATURE,
              config.MAX_TOKENS_RESPONSE, config.MODEL_NAME, config.API_RETRY_DELAY)
    agent = ExtractorAgent(config, logging, llm)

    # 4. & 5. Loop through chunks and extract data
    all_extracted_data = []
    for chunk in tqdm(relevant_chunks, desc=f"Processing chunks for {patent_id}"):
        raw_mentions, extracted_data = agent.run(chunk, patent_id, debug, debug_output_dir)
        if extracted_data:
            # Post-filter the results to ensure they meet the criteria
            for item in extracted_data:
                # тут попадала строка и get не работал
                if isinstance(item, dict):
                    if item.get("value") and item.get("molecule_name") and item.get("binding_metric") and item.get("protein_target_name"):
                        item["raw_mentions"] = raw_mentions  # Add the source mentions for debugging
                        all_extracted_data.append(item)

    logging.info(f"Extracted {len(all_extracted_data)} data points from patent {patent_id}.")
    
    # 6. Return all data
    return all_extracted_data
