from common_utils.config_llm import ConfigLLM

from common_utils.init_env import LLM_KEY, LLM_MODEL, LLM_URL, LLM_CHUNK_SIZE, LLM_CHUNK_OVERLAP, LLM_MAX_TOKEN

class ConfigAliasLLM(ConfigLLM):
    # --- API and Directory Configuration ---
    API_BASE_URL = LLM_URL
    API_KEY = LLM_KEY
    MODEL_NAME = LLM_MODEL
    TEMPERATURE = 0.3
    MAX_TOKENS_RESPONSE = LLM_MAX_TOKEN

    # --- Error Handling Configuration ---
    API_RETRY_ATTEMPTS = 3
    API_RETRY_DELAY = 1  # seconds

    # --- Chunking and Pre-filtering Configuration ---
    METRIC_REGEX_PATTERN = r""
    NEGATIVE_KEYWORDS_REGEX = r""
    CHUNK_CONTEXT_SIZE = LLM_CHUNK_SIZE
    CHUNK_OVERLAP = LLM_CHUNK_OVERLAP

    SYSTEM_PROMPT = """
    You are a chemistry nomenclature expert.
    Task: For each alias below, return the most common name of the molecule it refers to.
    If an alias is unknown or maps to multiple molecules, output “Not found”.
    """

    USER_PROMPT = """
    Alias list start:
    {alias_list}
    Alias list end
    
    Text:
    {patent_text}
    
    Return only in format "alias;; molecula_name" and nothing more
    """
