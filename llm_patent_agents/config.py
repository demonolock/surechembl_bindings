
# --- API and Directory Configuration ---
API_BASE_URL = "http://80.209.242.40:8000/v1"
API_KEY = "dummy-key"
MODEL_NAME = "llama-3.3-70b-instruct"
TEMPERATURE = 0.1
MAX_TOKENS_RESPONSE = 4096
DEBUG_OUTPUT_DIR = "debug_output"

# --- Error Handling Configuration ---
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY = 1  # seconds

# --- Chunking and Pre-filtering Configuration ---
METRIC_REGEX_PATTERN = r'\b(IC50|Ki|EC50|Kd|inhibition|binding assay)\b'
NEGATIVE_KEYWORDS_REGEX = r'\b(cytotoxicity|cell viability|cell growth|platelet count|viability assay|cytotoxic)\b'
CHUNK_CONTEXT_SIZE = 1500
CHUNK_OVERLAP = 300

# --- Prompt Templates ---
EXTRACTOR_FIND_PROMPT = """
You are a highly specialized research assistant. Your task is to find and list sentences or table rows from the provided text.
CRITICAL: A sentence/row is only relevant if it contains ALL of the following:
1. A bioactivity metric (IC50, Ki, Kd, EC50).
2. A specific numeric value associated with that metric (e.g., "10", "5.5", "<100").
3. A unit for that value (e.g., "nM", "uM", "%").

Do NOT include sentences that only describe methods or calculations in general terms. Only extract lines with concrete data points.
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
JSON format for each object:
{{
    "molecule_name": "name, ID or other identifictor of the molecule",
    "protein_target_name": "the name of the target protein as mentioned in the text",
    "protein_uniprot_id": "UniProt ID if available, else null",
    "protein_seq_id": "SEQ ID NO if available, else null",
    "binding_metric": "the metric type like IC50, Ki, KB, Kd, EC50",
    "value": "the numeric value as a string",
    "unit": "nM, uM, pM, or %"
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
