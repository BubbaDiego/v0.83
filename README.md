# v0.8

For an overview of the key modules and architecture, see
[SPECIFICATIONS.md](SPECIFICATIONS.md). This now includes the

[Monitor Core specification](monitor/monitor_module_spec.md).

## Quick Start

Create a virtual environment and install all dependencies:

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
The requirements list includes the `solana` and `solders` packages used for
wallet balance lookups.

This installs `pytest` and all other required packages. Run the app with:

```bash
python launch_pad.py
```
When the server starts, the console prints a clickable link to
`http://127.0.0.1:5000/` (in terminals that support hyperlinks) so you can open
the dashboard directly.

The `.flaskenv` file provides the usual Flask environment variables for
development. `PYTHONPATH` now points to the project root:

```bash
FLASK_APP=sonic_app.py
FLASK_ENV=development
FLASK_DEBUG=1
PYTHONPATH=.
```
If you have an older copy with an absolute `PYTHONPATH`, update or remove that
line before running `flask` commands.

Or execute the full test suite using:

```bash
pytest
```

### Debug Logging

To see verbose output from the console logger, pass `debug=True` when
configuring logging:

```python
from core.logging import configure_console_log
configure_console_log(debug=True)
```

Classes like `Cyclone` propagate this flag via their own `debug` parameter.

## Twilio Testing

To verify your Twilio credentials or trigger a Studio Flow, copy `.env.example` to
`.env` and fill in your details. Then run:

```bash
python scripts/twilio_run.py
```

The script loads credentials from the `.env` file (or environment variables) and
uses `scripts/twilio_test.py` to perform the authentication and optional flow
execution.

## ChatGPT API Test

To verify your OpenAI credentials, copy `.env.example` to `.env`, fill in your
`OPENAI_API_KEY`, and run:

```bash
python scripts/openai_test.py
```


The script automatically loads environment variables from `.env` (with
`.env.example` as a fallback).


The script sends a simple prompt to ChatGPT and prints the response. It exits
with status code `0` on success and `1` on failure.

## GPT Oracle

Run `python sonic_app.py` and navigate to `/GPT/chat` to open the oracle front end.
The page shows four buttons—`portfolio`, `alerts`, `prices`, and `system`—that
query the `/gpt/oracle/<topic>` API and display the reply using **OracleCore**.
OracleCore aggregates context, applies optional strategies, and sends the prompt
to GPT.

The API can be called directly as well:

```bash
curl "http://localhost:5000/gpt/oracle/portfolio?strategy=none"
```

Replace `portfolio` with any other topic to receive a short summary. Use the
`strategy` query parameter to apply a named strategy (defaults to `none`).

System queries now include the latest update timestamps along with recent
`death_log.txt` entries and any system alerts so GPT can report operational
issues.

### Personas

Oracle responses can adopt different tones. Specify a `persona` with the
`/gpt/oracle/<topic>` route or call the dedicated persona endpoint:

```bash
curl "http://localhost:5000/gpt/persona/gothic/portfolio?strategy=degen"
```

Built in personas include `default`, `gothic`, and `surfer`. Combine personas
with strategies like `cautious`, `safe`, `degen`, or `dynamic_hedging` for
fine‑tuned replies.


## Required Environment Variables

The application expects several environment variables for email and Twilio
integration. Create a `.env` file or export them in your shell before running
the app:

```
SMTP_SERVER=your.smtp.server
SMTP_PORT=587
SMTP_USERNAME=you@example.com
SMTP_PASSWORD=your_password
SMTP_DEFAULT_RECIPIENT=you@example.com

TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_PHONE=+1987654321
TWILIO_TO_PHONE=+1234567890
# Optional
TWILIO_FLOW_SID=your_flow_sid_here
JUPITER_API_BASE=https://perps-api.jup.ag
OPENAI_API_KEY=your_openai_key_here
```

`JUPITER_API_BASE` lets you override the default Jupiter endpoint if it changes.

## Twilio Monitor

The `twilio_monitor` runs as part of the background monitor suite. It uses
`CheckTwilioHeartbeartService` in dry‑run mode to verify that credentials are
valid without placing an actual call.

## Hedge Calculator

## Threshold Seeder
Default alert thresholds can still be populated using the dedicated module:

```bash
python -m data.threshold_seeder
```

However, the main database initializer now exposes the same functionality via

the `--seed-thresholds` flag, allowing all seeding tasks to be consolidated into
a single command.

## Exporting Alert Thresholds

Use the **Export** button on the Alert Thresholds page (or the
`/system/alert_thresholds/export` API endpoint) to save a JSON snapshot of the
current threshold limits to the `/config/alert_thresholds.json` file on the
server. These exported values are the limits the system uses when evaluating
alerts—they do **not** represent the current alerts themselves.

## Running `sonic_app.py`

The Flask dashboard can be started directly from the project root. Ensure that
all required environment variables above are set (either in a `.env` file or in
your shell) and then run:

```bash
python sonic_app.py
```

By default the server listens on `0.0.0.0:5000`. The startup message prints a clickable link to `http://127.0.0.1:5000/` (when your terminal supports ANSI hyperlinks). Use the `--monitor` flag to also launch the local monitor process in a separate console.


## Initializing the Database

To create the SQLite database and all required tables, run:

```bash
python scripts/initialize_database.py
```

The script creates `mother_brain.db` in the `data` directory (or the path set via
the `DB_PATH` environment variable) and ensures every table exists.  Additional
flags allow optional seeding and resets:

```bash
# wipe the DB and seed thresholds and wallets
python scripts/initialize_database.py --reset --seed-thresholds --seed-wallets

# run every available seeder
python scripts/initialize_database.py --all
```

If you encounter SQLite errors such as `file is not a database`, the
database file is likely corrupted. Rebuild it by running:

```bash
python scripts/initialize_database.py --reset
```

This removes the existing `mother_brain.db` and recreates all tables. You can
also call `StartUpService.run_all()` from `utils.startup_service` to perform the
same checks and initialization at startup.

**Existing Installations**

If you have an older database created before version 0.8.5, add the new `status` column manually:

```sql
ALTER TABLE positions ADD COLUMN status TEXT DEFAULT 'ACTIVE';
```

## Startup Service

`utils.startup_service` provides a unified `StartUpService` helper. Running
`StartUpService.run_all()` ensures the `mother_brain.db` database exists, checks
for required configuration files and creates the `logs/` and `data/` directories
if needed. Progress is shown via a simple dot spinner between steps. Environment
variables are automatically loaded from a `.env` file in the project root (with
`.env.example` as a fallback) before any checks run. When all checks pass a
short startup sound (`static/sounds/web_station_startup.mp3`) will play. On
failure the "death spiral" tone is used instead. Invoke this at application
launch to verify the environment is ready. The Launch Pad console exposes this
check via a **Startup Service** option in its main menu.

## Database Recovery

If the SQLite file becomes corrupted, you can rebuild it directly from the
Launch Pad utility:

```bash
python launch_pad.py
```

Open the **Operations** menu and choose **Recover Database**. This deletes the
damaged `mother_brain.db` and recreates it with the required tables.

You can perform the same reset from the command line:

```bash
python scripts/initialize_database.py --reset
```

Run this (or `StartUpService.run_all()` in `utils.startup_service`) whenever you
see errors like `file is not a database` to rebuild a corrupted DB file.

## Windows Branch Name Compatibility
If a remote branch name contains characters that are invalid on Windows (such as `>` or `:`), Git cannot create the local reference. Rename the branch on a Unix-like system or ask the author to rename it. For example:

```bash
git checkout codex/fix-->=-not-supported--error-in-apply_color
git branch -m codex/fix-not-supported-error-in-apply_color
git push origin :codex/fix-->=-not-supported--error-in-apply_color codex/fix-not-supported-error-in-apply_color
```

After renaming, Windows users can fetch the branch normally.

## auto_core Module

The `auto_core` package handles automated browser workflows for Jupiter's perpetuals trading UI. It builds on the ideas in the [automation white paper](sonic_labs/order_automation_white_paper.md), using Playwright to load a Chromium profile with the Phantom wallet extension. `auto_core` exposes helpers for launching a persistent context, navigating the site and approving Phantom pop‑ups so strategies can focus on trading logic.

### Playwright Setup with Phantom
Install Playwright and its browsers:
```bash
pip install playwright
playwright install
```
To load Phantom, specify the extension path and a profile directory when launching the browser:
```python
from playwright.sync_api import sync_playwright

phantom_path = "/path/to/phantom"
profile_dir = "/tmp/playwright/phantom-profile"

with sync_playwright() as pw:
    context = pw.chromium.launch_persistent_context(
        profile_dir,
        channel="chromium",
        headless=False,
        args=[
            f"--disable-extensions-except={phantom_path}",
            f"--load-extension={phantom_path}"
        ]
    )
    page = context.new_page()
    page.goto("https://jup.ag/perpetuals")
```
The persistent profile keeps Phantom unlocked between runs. Adjust `headless` and add `--headless=new` for server environments.

The collateral management process is documented in
[sonic_labs/collateral_management_playwright_white_paper.md](sonic_labs/collateral_management_playwright_white_paper.md).
`AutoCore` includes helpers for headless execution with optional user agent and
slow motion settings. Provide the Phantom extension ID to open the popup page
when running headless.
