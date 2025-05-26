import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List

from data.data_locker import DataLocker
from core.constants import DB_PATH
from .context_loader import get_context_messages


class GPTContextService:
    """Create GPT context messages based on request type."""

    def __init__(self, data_locker: Optional[DataLocker] = None, db_path: str = DB_PATH):
        self.logger = logging.getLogger(__name__)
        self.dl = data_locker or DataLocker(str(db_path))

    def _fetch_snapshots(self) -> Dict[str, Optional[dict]]:
        """Return current and previous portfolio snapshots."""
        current = self.dl.portfolio.get_latest_snapshot()
        history = self.dl.get_portfolio_history()
        previous = history[-2] if len(history) >= 2 else None
        return {"current": current, "previous": previous}

    def _build_analysis_payload(self, instructions: str = "") -> Dict[str, Any]:
        snaps = self._fetch_snapshots()
        payload = {
            "type": "gpt_analysis_bundle",
            "version": "1.0",
            "generated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "meta": {
                "type": "meta",
                "version": "1.0",
                "owner": "Geno",
                "strategy": "hedged, automated trading",
                "goal": "optimize exposure while minimizing risk",
                "notes": "Background context",
            },
            "definitions": {
                "type": "definitions",
                "metrics": {
                    "travel_percent": "Defines change from entry to current price",
                    "heat_index": "Composite risk metric",
                },
            },
            "alert_limits": {
                "alert_ranges": {
                    "heat_index_ranges": {
                        "enabled": True,
                        "low": 7.0,
                        "medium": 33.0,
                        "high": 66.0,
                    }
                }
            },
            "module_references": {
                "modules": {
                    "PositionCore": {"role": "Manages enrichment, snapshots, sync"},
                    "HedgeCalcServices": {"role": "Suggests hedge rebalancing"},
                }
            },
            "current_snapshot": snaps.get("current"),
            "previous_snapshot": snaps.get("previous"),
            "instructions_for_ai": instructions or "Analyze portfolio risk and improvements",
        }
        return payload

    def build_analysis_messages(self, instructions: str = "") -> List[Dict[str, str]]:
        payload = self._build_analysis_payload(instructions)
        return [
            {"role": "system", "content": "You are a portfolio analysis assistant."},
            {"role": "user", "content": json.dumps(payload)},
        ]

    def build_portfolio_messages(self) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": "You are a portfolio analysis assistant."}]
        messages.extend(get_context_messages())
        messages.append({"role": "user", "content": "Provide a portfolio analysis summary."})
        return messages

    def create_messages(self, request_type: str, instructions: str = "") -> List[Dict[str, str]]:
        """Return a list of GPT messages for the given request type."""
        if request_type == "analysis":
            return self.build_analysis_messages(instructions)
        if request_type == "portfolio":
            return self.build_portfolio_messages()
        raise ValueError(f"Unsupported request type: {request_type}")
