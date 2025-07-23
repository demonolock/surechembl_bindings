import time

import openai

class LLM:
    def __init__(self, api_retry_attempts, api_key, api_base_url, temperature, max_tokens_response, model_name,
                 api_retry_delay, logger):
        self.api_retry_attempts = api_retry_attempts
        self.api_retry_delay = api_retry_delay
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.temperature = temperature
        self.max_tokens_response = max_tokens_response
        self.model_name = model_name
        self.logger = logger

    def call_llm(self, prompt: str) -> str | None:
        """
        Calls the LLM API with retry logic.
        """
        for attempt in range(self.api_retry_attempts):
            try:
                client = openai.OpenAI(api_key=self.api_key, base_url=self.api_base_url)
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens_response,
                )
                # Correctly access the content from the response object
                if response.choices and response.choices[0].message:
                    return response.choices[0].message.content
                else:
                    self.logger.error("Invalid response structure from API.")
                    return None
            except Exception as e:
                self.logger.error(f"API call failed on attempt {attempt + 1}: {e}")
                if attempt < self.api_retry_attempts - 1:
                    time.sleep(self.api_retry_attempts)
                else:
                    self.logger.error("All API retry attempts failed.")
                    return None