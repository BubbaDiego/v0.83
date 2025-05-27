# 🧠 GPT Core Specification

> Version: v1.0
> Scope: Python modules powering GPT interaction and the chat UI
> Author: CoreOps 🥷

---

## 📂 Module Layout

```txt
gpt/
├── gpt_core.py            # Core GPT utilities
├── gpt_bp.py              # JSON API endpoints
├── chat_gpt_bp.py         # Web UI blueprint
├── context_loader.py      # Loads JSON context snippets
├── create_gpt_context_service.py # Message builder
├── templates/chat_gpt.html # Front-end interface
```

---

## 🎛️ GPTCore

`GPTCore` orchestrates all communication with the OpenAI API. It loads environment variables, fetches data via `DataLocker`, and exposes helper methods for various queries.

### Key sections

```python
class GPTCore:
    """Core utilities for interacting with GPT."""
    def __init__(self, db_path: str = DB_PATH):
        load_dotenv()
        self.logger = logging.getLogger(__name__)
        self.data_locker = DataLocker(str(db_path))
        self.client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))
```
【F:gpt/gpt_core.py†L16-L23】

### Payload construction

`build_payload()` gathers the latest portfolio snapshots and prepares a JSON bundle with meta information, alert limits, and module references.

```python
    def build_payload(self, instructions: str = "") -> Dict[str, Any]:
        snaps = self._fetch_snapshots()
        payload = {
            "type": "gpt_analysis_bundle",
            "version": "1.0",
            "generated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "meta": { ... },
            "definitions": { ... },
            "alert_limits": { ... },
            "module_references": { ... },
            "current_snapshot": snaps.get("current"),
            "previous_snapshot": snaps.get("previous"),
            "instructions_for_ai": instructions or "Analyze portfolio risk and improvements",
        }
        return payload
```
【F:gpt/gpt_core.py†L31-L71】

### Chat helpers

The core exposes multiple question methods that return a text reply from GPT:

```python
    def ask_gpt_about_portfolio(self) -> str:
        ...
        messages = [
            {"role": "system", "content": "You are a portfolio analysis assistant."},
            ...
        ]
        response = self.client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
        return response.choices[0].message.content.strip()
```
【F:gpt/gpt_core.py†L88-L107】

Other helper methods `ask_gpt_about_alerts`, `ask_gpt_about_prices`, and `ask_gpt_about_system` follow the same pattern to provide summaries from their respective datasets.【F:gpt/gpt_core.py†L111-L160】

## 🔮 Oracle

`oracle.py` defines a small helper that bundles context for quick queries.

```python
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
```
【F:gpt/oracle.py†L7-L21】

`get_context()` returns a list of chat messages based on the topic, pulling data
from `DataLocker` when required.
【F:gpt/oracle.py†L23-L56】

---

## 🗂️ Context Loading

`context_loader.py` loads JSON files bundled under `gpt/data` and converts them into system messages for ChatGPT.

```python
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def get_context_data() -> dict:
    files = ["gpt_meta_input.json", "gpt_definitions_input.json", "gpt_alert_limits_input.json", "gpt_module_references.json", "snapshot_sample.json"]
    data = {}
    for fname in files:
        content = _load_json(fname)
        if content:
            data[fname] = content
    return data
```
【F:gpt/context_loader.py†L7-L38】

The helper `get_context_messages()` wraps each loaded JSON object into a ChatGPT system message.【F:gpt/context_loader.py†L41-L45】

---

## 💬 Flask Blueprints

### `gpt_bp`
Provides JSON API endpoints.

- `POST /gpt/analyze` → build a payload and ask GPT for analysis.
- `GET /gpt/portfolio` → use static context files for a portfolio summary.
 - `GET /gpt/oracle/<topic>` → call `Oracle` for a quick summary of `portfolio`, `alerts`, `prices`, or `system`.

Implementation excerpt:
```python
@gpt_bp.route('/gpt/analyze', methods=['POST'])
def analyze():
    instructions = request.json.get('prompt', '') if request.is_json else ''
    core = GPTCore()
    result = core.analyze(instructions)
    return jsonify({"reply": result})
```
【F:gpt/gpt_bp.py†L12-L18】

### `chat_gpt_bp`
Serves the interactive chat page and handles message posts.

```python
chat_gpt_bp = Blueprint(
    "chat_gpt_bp",
    __name__,
    url_prefix="/GPT",
    template_folder="../templates",
)
```
【F:gpt/chat_gpt_bp.py†L24-L29】

The `GET /GPT/chat` route renders `chat_gpt.html` while `POST /GPT/chat` forwards user messages to the OpenAI API and returns the reply along with token usage stats.【F:gpt/chat_gpt_bp.py†L31-L74】

---

## 🖥️ Chat UI

`templates/chat_gpt.html` provides a two‑panel interface: an oracle panel with preset buttons and a chat panel. Styles and behavior are embedded in the template.

```html
<div class="oracle-btns d-flex justify-content-around mb-3">
  <button class="oracle-btn btn btn-outline-primary" data-topic="portfolio" title="Ask about portfolio">📂</button>
  <button class="oracle-btn btn btn-outline-secondary" data-topic="alerts" title="Ask about alerts">🚨</button>
  <button class="oracle-btn btn btn-outline-secondary" data-topic="prices" title="Ask about prices">💲</button>
  <button class="oracle-btn btn btn-outline-secondary" data-topic="system" title="Ask about system">🖥️</button>
</div>
<div id="oracleOutput" class="oracle-output"></div>
```
【F:templates/chat_gpt.html†L112-L121】

The chat panel contains a scrollable message window and input box.

```html
<div class="chat-window" id="chatWindow">
  <!-- Chat messages will appear here -->
</div>
<div class="input-area">
  <input type="text" id="userInput" placeholder="Type your message here..." />
  <button id="sendBtn">Send</button>
  <button id="portfolioBtn">Ask Portfolio</button>
</div>
```
【F:templates/chat_gpt.html†L132-L139】

JavaScript hooks the buttons to API routes, appending messages to the window and tracking token usage.

```javascript
sendBtn.addEventListener('click', async () => {
  const message = userInput.value.trim();
  if (!message) return;
  addMessage(message, 'user');
  userInput.value = '';
  const res = await fetch('{{ url_for('chat_gpt_bp.chat_post') }}', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });
  const data = await res.json();
  addMessage(data.reply, 'bot');
  if (data.usage) {
    tokenInfo.textContent = `Prompt tokens: ${data.usage.prompt_tokens}, Completion tokens: ${data.usage.completion_tokens}, Total: ${data.usage.total_tokens}`;
  }
});
```
【F:templates/chat_gpt.html†L181-L199】

---

## 📈 Usage

1. Mount `gpt_bp` and `chat_gpt_bp` in the Flask app.
2. Navigate to `/GPT/chat` for the web interface or POST to `/gpt/analyze` to receive a JSON response.
3. Context files under `gpt/data` provide default prompts and limits; update them as needed to tune results.

This specification captures the GPT integration and UI components so that another GPT model can reason about the codebase or generate enhancements.

