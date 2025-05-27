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
    core = GPTCore()
    if topic == 'portfolio':
        result = core.ask_gpt_about_portfolio()
    elif topic == 'alerts':
        result = core.ask_gpt_about_alerts()
    elif topic == 'prices':
        result = core.ask_gpt_about_prices()
    elif topic == 'system':
        result = core.ask_gpt_about_system()
    else:
        return jsonify({"error": "Unknown topic"}), 400
    return jsonify({"reply": result})
