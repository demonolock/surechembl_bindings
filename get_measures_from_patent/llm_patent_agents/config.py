import os

from common_utils.init_env import LLM_KEY, LLM_MODEL, LLM_URL

# --- API and Directory Configuration ---
API_BASE_URL = LLM_URL
API_KEY = LLM_KEY
MODEL_NAME = LLM_MODEL
TEMPERATURE = 0.1
MAX_TOKENS_RESPONSE = 131072
DEBUG_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "debug_output"
)

# --- Error Handling Configuration ---
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 1  # seconds

# --- Chunking and Pre-filtering Configuration ---
METRIC_REGEX_PATTERN = r"\b(IC[\s_-]*50|IC₅₀|Ki|Kd|EC[\s_-]*50|EC₅₀|pIC[\s_-]*50|pIC₅₀|pEC[\s_-]*50|pEC₅₀|pKi|pKd|logIC50|log[\s]*\([\s]*IC50[\s]*\)|-log[\s]*\([\s]*IC50[\s]*\)|logKi|log[\s]*\([\s]*Ki[\s]*\)|-log[\s]*\([\s]*Ki[\s]*\)|logKd|log[\s]*\([\s]*Kd[\s]*\)|-log[\s]*\([\s]*Kd[\s]*\)|logEC50|log[\s]*\([\s]*EC50[\s]*\)|-log[\s]*\([\s]*EC50[\s]*\)|inhibition[\s-]*constant|dissociation[\s-]*constant|binding[\s-]*constant|half[\s-]*maximal[\s-]*inhibitory[\s-]*concentration|half[\s-]*maximal[\s-]*effective[\s-]*concentration|binding[\s-]*assay)\b"
NEGATIVE_KEYWORDS_REGEX = r"\b(cytotoxicity|cell viability|cell growth|platelet count|viability assay|cytotoxic)\b"
CHUNK_CONTEXT_SIZE = 1500
CHUNK_OVERLAP = 300

# --- Prompt Templates ---
EXTRACTOR_FIND_PROMPT = """
You are a highly specialized research assistant. Your task is to find and list sentences or table rows from the provided text.

CRITICAL: A sentence/row is only relevant if it contains ALL FOUR of the following components:
1. A specific molecule name, ID or other identifier.
2. A bioactivity metric (e.g., IC50, Ki, Kd, EC50, pIC50, pEC50, pKi, pKd).
3. A specific numeric value for that metric (e.g., "10", "5.5", "<100").
4. A unit for that value (e.g., "nM", "uM", "%").

Extract enough contex to identify specific molecule or metric. Do NOT include sentences that only describe methods or calculations in general terms.
Return ONLY the raw sentences/lines, one per line.

--- Text Snippet to Analyze ---
{text_chunk}
---
"""

EXTRACTOR_FORMAT_PROMPT = """
You are a data formatting specialist. Based on the list of raw sentences/lines provided below, convert each finding into a structured JSON object. The final output must be a single JSON list `[]`.

Rules:
1. Extract data EXACTLY as it is written. Do not change or normalize values.
2. For the 'value' field, if the text contains an operator like '<10' or '>1000', extract it as a string, e.g., "<10".
3. If a value for a field is not present in the text, the value for that key must be null.
4. For "molecule_name", extract the most specific identifier available. If the text mentions both a general class and a specific ID, extract the specific ID.
5. For protein information, be as specific as possible.

JSON format for each object:
{{
    "molecule_name": "name, ID or other identifier of the molecule. If not found, use null.",
    "protein_target_name": "the name of the target protein. If not found, use null.",
    "binding_metric": "the metric type like IC50, Ki, Kd, EC50, pIC50, pEC50, pKi, pKd",
    "value": "the numeric value as a string",
    "unit": "the unit for the value (e.g., nM, uM, pM, %). If not found, use null."
}}

--- Raw Sentences/Lines to Format ---
{raw_mentions}
---
"""

JSON_CORRECTION_PROMPT = """
The following text is not a valid JSON. It has syntax errors.
Please correct the text so it becomes a valid JSON list `[]` of objects, without changing the data content.
Return ONLY the corrected, valid JSON.

--- Invalid Text ---
{invalid_json_text}
---
"""
