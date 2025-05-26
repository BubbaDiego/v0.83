import os
import logging
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

_API_KEY = (os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_KEY") or "").strip()
client = OpenAI(api_key=_API_KEY)

class GPTCore:
    """Interface to perform portfolio analysis via OpenAI models."""

    MODEL_NAME = "gpt-3.5-turbo"

    def analyze(self, instructions: str) -> str:
        """Return GPT analysis for the provided instructions."""
        prompt = (instructions or "").strip()
        logger.debug(f"Analyzing with prompt: {prompt!r}")
        messages = [
            {"role": "system", "content": "You are a helpful financial assistant."},
            {"role": "user", "content": prompt},
        ]
        try:
            response = client.chat.completions.create(model=self.MODEL_NAME, messages=messages)
            logger.debug("Received GPT analysis response")
            return response.choices[0].message.content.strip()
        except Exception as e:  # pragma: no cover - rely on OpenAI client
            logger.exception("GPT analysis failed")
            return f"An error occurred: {e}"
