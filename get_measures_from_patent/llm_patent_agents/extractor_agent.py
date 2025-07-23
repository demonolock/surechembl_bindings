import json
import os
import re

from common_utils.call_llm import LLM


class ExtractorAgent:
    def __init__(self, config, logging, llm: LLM):
        self.config = config
        self.logging = logging
        self.llm = llm

    """
    An agent that extracts structured data from a text chunk using a two-step LLM process.
    """
    def run(self, text_chunk: str, patent_id: str, debug: bool = False,
            debug_output_dir: str | None = None) -> tuple[str | None, list[dict]]:
        """
        Runs the two-step extraction process.
        Returns the raw mentions and the extracted data.
        """
        if debug and debug_output_dir is None:
            debug_output_dir = self.config.DEBUG_OUTPUT_DIR

        # Step 1: Find raw mentions
        find_prompt = self.config.EXTRACTOR_FIND_PROMPT.format(text_chunk=text_chunk)
        raw_mentions = self.llm.call_llm(find_prompt)

        if not raw_mentions or "no relevant" in raw_mentions.lower():
            self.logging.info("No raw mentions found by the extractor agent.")
            return None, []

        # Debugging: Save raw mentions
        if debug:
            debug_dir = os.path.join(debug_output_dir, patent_id)
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, "02_extractor_outputs.jsonl"), "a") as f:
                f.write(json.dumps({"raw_mentions": raw_mentions}) + "\n")

        # Step 2: Format into JSON
        format_prompt = self.config.EXTRACTOR_FORMAT_PROMPT.format(raw_mentions=raw_mentions)
        json_response = self.llm.call_llm(format_prompt)

        if not json_response:
            self.logging.error("Failed to get a formatted JSON response from the LLM.")
            return raw_mentions, []

        # JSON Self-Correction
        extracted_data = []
        try:
            json_to_parse = self._extract_json_from_response(json_response)
            if not json_to_parse:
                raise json.JSONDecodeError("No JSON found in the LLM response", json_response, 0)
            extracted_data = json.loads(json_to_parse)
        except json.JSONDecodeError:
            self.logging.warning(f"Initial JSON parsing failed. Raw response:\n{json_response}\nAttempting self-correction.")
            correction_prompt = self.config.JSON_CORRECTION_PROMPT.format(invalid_json_text=json_response)
            corrected_json_response = self.llm.call_llm(correction_prompt)
            if not corrected_json_response:
                self.logging.error("LLM failed to provide a corrected JSON.")
                return raw_mentions, []
            try:
                json_to_parse = self._extract_json_from_response(corrected_json_response)
                if not json_to_parse:
                    raise json.JSONDecodeError("No JSON found in the corrected LLM response", corrected_json_response, 0)
                extracted_data = json.loads(json_to_parse)
                json_response = corrected_json_response # Use corrected version for debug log
            except json.JSONDecodeError as e:
                self.logging.error(f"Failed to parse JSON even after correction: {e}")
                self.logging.error(f"Original response: {json_response}")
                self.logging.error(f"Corrected response: {corrected_json_response}")
                return raw_mentions, []

        # Debugging: Save final JSON
        if debug and extracted_data:
            debug_dir = os.path.join(debug_output_dir, patent_id)
            with open(os.path.join(debug_dir, "02_extractor_outputs.jsonl"), "a") as f:
                f.write(json.dumps({"final_json": extracted_data}) + "\n")

        return raw_mentions, extracted_data


    def _extract_json_from_response(self, response_text: str) -> str | None:
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

        self.logging.warning("Could not find a JSON block in the response.")
        return None
