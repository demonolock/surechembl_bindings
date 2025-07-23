from common_utils.config_llm import ConfigLLM


class ConfigAliasLLM(ConfigLLM):
    # --- API and Directory Configuration ---
    API_BASE_URL = "http://80.209.242.40:8000/v1"
    API_KEY = "dummy-key"
    MODEL_NAME = "llama-3.3-70b-instruct"
    TEMPERATURE = 0.3
    MAX_TOKENS_RESPONSE = 4096

    # --- Error Handling Configuration ---
    API_RETRY_ATTEMPTS = 3
    API_RETRY_DELAY = 1  # seconds

    # --- Chunking and Pre-filtering Configuration ---
    METRIC_REGEX_PATTERN = r""
    NEGATIVE_KEYWORDS_REGEX = r""
    CHUNK_CONTEXT_SIZE = 1500
    CHUNK_OVERLAP = 300

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
