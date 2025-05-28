import logging
from flask import Blueprint, jsonify, request

from .gpt_core import GPTCore
from .persona_manager import PersonaManager
from oracle_core import OracleCore

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


@gpt_bp.route('/gpt/oracle/query', methods=['GET'])
def oracle_query():
    """Query GPT using a persona and optional topic."""
    persona_name = request.args.get('persona', '').strip()
    if not persona_name:
        return jsonify({"error": "persona parameter required"}), 400
    topic = request.args.get('topic', 'portfolio').strip() or 'portfolio'

    core = GPTCore()
    pm = PersonaManager()
    try:
        persona = pm.get(persona_name)
    except KeyError:
        return jsonify({"error": "Unknown persona"}), 400

    oracle = OracleCore(core.data_locker)
    oracle.client = core.client

    if topic not in oracle.handlers:
        return jsonify({"error": "Unknown topic"}), 400

    handler = oracle.handlers[topic]
    context = handler.get_context()

    instructions = persona.instructions or OracleCore.DEFAULT_INSTRUCTIONS.get(topic, "Assist the user.")
    system_msg = persona.system_message or OracleCore.DEFAULT_SYSTEM_MESSAGES.get(topic, "You assist the user.")

    messages = oracle.build_prompt(topic, context, instructions)
    if messages:
        messages[0]["content"] = system_msg

    try:
        reply = oracle.query_gpt(messages)
        return jsonify({"reply": reply})
    except Exception as ex:  # pragma: no cover - depends on OpenAI API
        logger.exception("Oracle query failed: %s", ex)
        return jsonify({"error": str(ex)}), 500
