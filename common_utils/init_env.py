import os

LLM_KEY = os.environ["LLM_KEY"]
LLM_URL = os.environ["LLM_URL"]
LLM_MODEL = os.environ["LLM_MODEL"]
LLM_TEMPERATURE = float(os.environ["LLM_TEMPERATURE"])
LLM_MAX_TOKEN = int(os.environ["LLM_MAX_TOKEN"])
LLM_CHUNK_SIZE = int(os.environ["LLM_CHUNK_SIZE"])
LLM_CHUNK_OVERLAP = int(os.environ["LLM_CHUNK_OVERLAP"])
