import json
from typing import List

from gpt.context_loader import get_context_messages


class Oracle:
    """Bundle context and instructions for GPT queries."""

    def __init__(self, topic: str, data_locker, instructions: str = ""):
        self.topic = topic
        self.data_locker = data_locker
        self.instructions = instructions or self.default_instructions()

    def default_instructions(self) -> str:
        return {
            "portfolio": "Provide a portfolio analysis summary.",
            "alerts": "Summarize the current alert state.",
            "prices": "Summarize the market trends.",
            "system": "Summarize the system health status.",
        }.get(self.topic, "Assist the user.")

    def get_context(self) -> List[dict]:
        """Return GPT chat messages based on the requested topic."""
        static_context = get_context_messages()

        if self.topic == "portfolio":
            return [
                {"role": "system", "content": "You are a portfolio analysis assistant."},
                *static_context,
                {"role": "user", "content": self.instructions},
            ]

        if self.topic == "alerts":
            alerts = self.data_locker.alerts.get_all_alerts()[:20]
            return [
                {"role": "system", "content": "You summarize alert information."},
                {"role": "system", "content": json.dumps({"alerts": alerts})},
                {"role": "user", "content": self.instructions},
            ]

        if self.topic == "prices":
            prices = self.data_locker.prices.get_all_prices()[:20]
            return [
                {"role": "system", "content": "You summarize price information."},
                {"role": "system", "content": json.dumps({"prices": prices})},
                {"role": "user", "content": self.instructions},
            ]

        if self.topic == "system":
            system = self.data_locker.get_last_update_times()
            return [
                {"role": "system", "content": "You report system status."},
                {"role": "system", "content": json.dumps(system)},
                {"role": "user", "content": self.instructions},
            ]

        raise ValueError(f"Unsupported topic: {self.topic}")

    def to_dict(self) -> dict:
        """Return a JSON serializable representation of the oracle request."""
        return {
            "topic": self.topic,
            "instructions": self.instructions,
            "context": self.get_context(),
        }
