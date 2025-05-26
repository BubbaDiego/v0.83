import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

from data.data_locker import DataLocker
from core.constants import DB_PATH
from .gpt_context_service import GPTContextService


class GPTCore:
    """Core utilities for interacting with GPT."""

    def __init__(self, db_path: str = DB_PATH):
        load_dotenv()
        self.logger = logging.getLogger(__name__)
        self.data_locker = DataLocker(str(db_path))
        self.client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))
        self.context_service = GPTContextService(self.data_locker)

    def analyze(self, instructions: str = "") -> str:
        messages = self.context_service.create_messages("analysis", instructions)
        self.logger.debug("Sending payload to GPT")
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", messages=messages
            )
            reply = response.choices[0].message.content.strip()
            self.logger.debug("Received reply from GPT")
            return reply
        except Exception as e:  # pragma: no cover - depends on OpenAI API
            self.logger.exception(f"GPT analysis failed: {e}")
            return f"Error: {e}"

    def ask_gpt_about_portfolio(self) -> str:
        """Use standard JSON context files to query GPT about the portfolio."""
        messages = self.context_service.create_messages("portfolio")
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo", messages=messages
            )
            reply = response.choices[0].message.content.strip()
            self.logger.debug("Received portfolio reply from GPT")
            return reply
        except Exception as e:  # pragma: no cover - depends on OpenAI API
            self.logger.exception(f"GPT portfolio query failed: {e}")
            return f"Error: {e}"

