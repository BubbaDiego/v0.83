from typing import Dict

from .oracle_data_service import OracleDataService


class PositionsTopicHandler:
    """Provide positions context for GPT."""

    output_key = "positions"
    system_message = "You summarize position information."

    def __init__(self, data_locker):
        self.data_service = OracleDataService(data_locker)

    def get_context(self) -> Dict:
        positions = self.data_service.fetch_positions()
        return {self.output_key: positions}
