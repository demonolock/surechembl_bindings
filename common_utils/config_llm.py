import os
from common_utils.init_env import LLM_KEY, LLM_MODEL, LLM_URL, LLM_TEMPERATURE, LLM_MAX_TOKEN

class ConfigLLM:
    # --- API and Directory Configuration ---
    API_BASE_URL = LLM_URL
    API_KEY = LLM_KEY
    MODEL_NAME = LLM_MODEL
    TEMPERATURE = LLM_TEMPERATURE
    MAX_TOKENS_RESPONSE = LLM_MAX_TOKEN
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

    SYSTEM_PROMPT = ""
    USER_PROMPT = ""
