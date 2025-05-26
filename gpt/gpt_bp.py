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
