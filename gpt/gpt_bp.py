import logging
from flask import Blueprint, jsonify, request

from .gpt_core import GPTCore

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

gpt_bp = Blueprint('gpt_bp', __name__)


@gpt_bp.route('/gpt/analyze', methods=['POST'])
def analyze():
    """Endpoint to analyze portfolio data with GPT."""
    instructions = request.json.get('prompt', '') if request.is_json else ''
    core = GPTCore()
    result = core.analyze(instructions)
    return jsonify({"reply": result})


@gpt_bp.route('/gpt/portfolio', methods=['GET'])
def ask_portfolio():
    """Return GPT analysis using standard context files."""
    core = GPTCore()
    result = core.ask_gpt_about_portfolio()
    return jsonify({"reply": result})


@gpt_bp.route('/gpt/oracle/<topic>', methods=['GET'])
def oracle(topic: str):
    """Handle oracle queries for various topics."""
    strategy = request.args.get("strategy", "none")
    core = GPTCore()
    strategy = request.args.get("strategy")
    try:
        result = core.ask_oracle(topic, strategy)
        return jsonify({"reply": result})
    except ValueError:
        return jsonify({"error": "Unknown topic"}), 400


@gpt_bp.route('/gpt/oracle/query', methods=['POST'])
def oracle_query():
    """Return persona-aware modifiers for a topic."""
    data = request.get_json() or {}
    topic = data.get("topic")
    persona = data.get("persona")
    if not topic:
        return jsonify({"error": "Missing topic"}), 400

    base_mods = {
        "distanceWeight": 0.6,
        "leverageWeight": 0.3,
        "collateralWeight": 0.1,
    }
    from oracle_core.persona_manager import PersonaManager

    if persona:
        manager = PersonaManager()
        try:
            mods = manager.merge_modifiers(base_mods, persona)
        except KeyError:
            return jsonify({"error": "Unknown persona"}), 400
    else:
        mods = base_mods

    return jsonify({"reply": {"topic": topic, "modifiers": mods}})
