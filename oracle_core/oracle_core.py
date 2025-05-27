import json
import os
from typing import Dict, List, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None

from .strategy_manager import StrategyManager
from .portfolio_topic_handler import PortfolioTopicHandler
from .alerts_topic_handler import AlertsTopicHandler
from .prices_topic_handler import PricesTopicHandler
from .system_topic_handler import SystemTopicHandler


class OracleCore:
    """Main orchestrator for GPT oracle queries."""

    DEFAULT_SYSTEM_MESSAGES = {
        "portfolio": "You are a portfolio analysis assistant.",
        "alerts": "You summarize alert information.",
        "prices": "You summarize price information.",
        "system": "You report system status.",
    }

    DEFAULT_INSTRUCTIONS = {
        "portfolio": "Provide a portfolio analysis summary.",
        "alerts": "Summarize the current alert state.",
        "prices": "Summarize the market trends.",
        "system": "Summarize the system health status.",
    }

    def __init__(self, data_locker):
        self.data_locker = data_locker
        if OpenAI:
            api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_KEY") or ""
            self.client = OpenAI(api_key=api_key) if api_key else None
        else:
            self.client = None
        self.strategy_manager = StrategyManager()
        self.handlers: Dict[str, object] = {}
        self.register_topic_handler("portfolio", PortfolioTopicHandler(data_locker))
        self.register_topic_handler("alerts", AlertsTopicHandler(data_locker))
        self.register_topic_handler("prices", PricesTopicHandler(data_locker))
        self.register_topic_handler("system", SystemTopicHandler(data_locker))

    # public API
    def register_topic_handler(self, name: str, handler: object):
        self.handlers[name] = handler

    def build_prompt(self, topic: str, context: Dict, instructions: str) -> List[Dict]:
        system_msg = self.DEFAULT_SYSTEM_MESSAGES.get(topic, "You assist the user.")
        return [
            {"role": "system", "content": system_msg},
            {"role": "system", "content": json.dumps(context)},
            {"role": "user", "content": instructions},
        ]

    def query_gpt(self, messages: List[Dict]) -> str:
        if self.client is None:
            raise RuntimeError("OpenAI client not configured")
        response = self.client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
        return response.choices[0].message.content.strip()

    def ask(self, topic: str, strategy_name: Optional[str] = None) -> str:
        if topic not in self.handlers:
            raise ValueError(f"Unsupported topic: {topic}")
        handler = self.handlers[topic]
        context = handler.get_context()
        instructions = self.DEFAULT_INSTRUCTIONS.get(topic, "Assist the user.")
        if strategy_name:
            strategy = self.strategy_manager.get(strategy_name)
            context = strategy.apply(context)
            instructions = strategy.instructions or instructions
        messages = self.build_prompt(topic, context, instructions)
        return self.query_gpt(messages)

    def to_dict(self, topic: str, strategy_name: Optional[str] = None) -> Dict:
        if topic not in self.handlers:
            raise ValueError(f"Unsupported topic: {topic}")
        handler = self.handlers[topic]
        context = handler.get_context()
        instructions = self.DEFAULT_INSTRUCTIONS.get(topic, "Assist the user.")
        if strategy_name:
            strategy = self.strategy_manager.get(strategy_name)
            context = strategy.apply(context)
            instructions = strategy.instructions or instructions
        messages = self.build_prompt(topic, context, instructions)
        return {"topic": topic, "messages": messages}
