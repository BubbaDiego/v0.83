from __future__ import annotations

import sys
import contextlib
import os
import importlib
import re
from pathlib import Path
import pytest
from core.core_imports import log

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    console = Console()
except Exception:  # pragma: no cover - rich optional
    Console = None
    Panel = None
    Table = None
    console = None


class TestCore:
    """Utility to run pytest with rich reporting."""

    def __init__(self, report_dir: str | Path = "reports", default_pattern: str = "tests/test_*.py") -> None:
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
        self.default_pattern = default_pattern

    # ------------------------------------------------------------------
    def run_all(self) -> None:
        """Run all tests matching the default pattern."""
        self.run_glob(self.default_pattern)

    def run_glob(self, pattern: str | None = None) -> None:
        """Discover test files matching *pattern* and run them."""
        pattern = pattern or self.default_pattern
        files = [
            p
            for p in Path(".").rglob(pattern)
            # Exclude common virtual environment directories
            if not any(part in {".venv", "venv", "site-packages"} for part in p.parts)
        ]
        if not files:
            log.warning(f"⚠️ No test files found for pattern: {pattern}", source="TestCore")
            return
        self.run_files(files)

    def run_files(self, files: list[str | Path]) -> None:
        """Execute pytest for the provided *files* with reporting enabled."""
        html_report = self.report_dir / "last_test_report.html"
        json_report = self.report_dir / "last_test_report.json"
        txt_log = self.report_dir / "last_test_log.txt"

        log.banner(f"🧪 Test Run Started ({len(files)} file(s))")
        log.info(f"⏱ Running: {[str(f) for f in files]}", source="TestCore")

        args = [*[str(f) for f in files], "-vv", "-s", "--tb=short", "-rA"]

        # Include optional plugins only if they are installed. This avoids
        # ``pytest`` failing when a plugin is referenced but not available in
        # the environment.
        for plugin in ["pytest_sugar", "pytest_spec", "pytest_console_scripts"]:
            if importlib.util.find_spec(plugin) is not None:
                args.extend(["-p", plugin])

        # ``pytest-html`` provides ``--html`` and ``--self-contained-html``.
        # These options must only be passed when the plugin is available.
        if importlib.util.find_spec("pytest_html") is not None:
            args.extend([
                f"--html={html_report}",
                "--self-contained-html",
            ])

        # ``pytest-json-report`` exposes the ``--json-report`` options. Avoid
        # using them when the plugin cannot be imported.
        if importlib.util.find_spec("pytest_jsonreport") is not None:
            args.extend([
                "--json-report",
                f"--json-report-file={json_report}",
            ])



        # Disable auto-loading of external plugins. Some external pytest
        # plugins may rely on optional dependencies that are not installed in
        # the environment, leading to import errors. Only the explicitly
        # specified plugins should be loaded during the test run.
        os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"

        with open(txt_log, "w", encoding="utf-8") as f, \
             contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            result = pytest.main(args)

        # After test run, parse results for a concise summary
        passed = failed = skipped = 0
        summary_lines = []
        try:
            import re
            pattern = re.compile(r"(PASSED|FAILED|ERROR|SKIPPED)\s+(\S+::\S+)")
            with open(txt_log, "r", encoding="utf-8") as lf:
                for line in lf:
                    match = pattern.search(line)
                    if match:
                        outcome, test_id = match.groups()
                        summary_lines.append(f"{test_id} {outcome}")
                        if outcome == "PASSED":
                            passed += 1
                        elif outcome in ("FAILED", "ERROR"):
                            failed += 1
                        elif outcome == "SKIPPED":
                            skipped += 1
        except Exception as e:  # pragma: no cover - summary best effort
            log.error(f"Failed to parse log summary: {e}", source="TestCore")

        for line in summary_lines:
            if line.endswith("PASSED"):
                log.success(f"✅ {line}", source="TestCore")
            elif line.endswith("FAILED") or line.endswith("ERROR"):
                log.error(f"❌ {line}", source="TestCore")
            elif line.endswith("SKIPPED"):
                log.warning(f"⚠️ {line}", source="TestCore")

        log.banner("Test Summary")
        log.info(
            f"✅ Passed: {passed}  ❌ Failed: {failed}  ⚠️ Skipped: {skipped}",
            source="TestCore",
        )

        total = passed + failed + skipped
        if total:
            pct = passed / total * 100
            log.info(
                f"🔢 Pass Rate: {pct:.1f}% ({passed}/{total})",
                source="TestCore",
            )

        if result == 0:
            log.success("✅ All tests completed!", source="TestCore")
        else:
            log.error("❌ Test run failed.", source="TestCore")
            try:
                with open(txt_log, "r", encoding="utf-8") as lf:
                    last_lines = lf.readlines()[-20:]
                print("\n==== ERROR DETAILS ====")
                for line in last_lines:
                    print(line.rstrip())
                print("=======================\n")
            except Exception as e:
                log.error(f"Failed to read log file: {e}", source="TestCore")

        log.info(f"📄 HTML Report: {html_report}", source="TestCore")
        log.info(f"🪵 Log File:    {txt_log}", source="TestCore")
        self._open_html_report(html_report)

    # ------------------------------------------------------------------
    def test_alert_core(self) -> None:
        """Run all AlertCore test cases."""
        self.run_glob("alert_core/**/test_*.py")

    # ------------------------------------------------------------------
    def pick_and_run_tests(self) -> None:
        """Allow user to pick specific tests to run."""
        tests = [
            p
            for p in Path("tests").rglob("test_*.py")
            if not any(part in {".venv", "venv", "site-packages"} for part in p.parts)
        ]
        if not tests:
            print("No tests found.")
            return
        tests = sorted(tests)
        for i, t in enumerate(tests, 1):
            print(f"{i}) {t}")
        choice = input("Select tests (e.g., 1,2,7) or 'q' to cancel: ").strip()
        if not choice or choice.lower() == "q":
            return
        import re
        nums = re.findall(r"\d+", choice)
        selected = []
        for n in nums:
            idx = int(n) - 1
            if 0 <= idx < len(tests):
                selected.append(tests[idx])
        # Remove duplicates while preserving order
        selected = list(dict.fromkeys(selected))
        if not selected:
            print("No valid selections.")
            return
        print("Running selected tests:")
        for s in selected:
            print(f"- {s}")
        self.run_files(selected)

    # ------------------------------------------------------------------
    def _open_html_report(self, report_path: Path) -> None:
        """Open *report_path* in a browser if possible."""
        if not report_path.exists():
            return
        try:
            import webbrowser
            webbrowser.open(report_path.resolve().as_uri())
        except Exception:
            pass

    # ------------------------------------------------------------------
    def interactive_menu(self) -> None:
        """Interactive CLI for running tests with optional Rich formatting."""
        while True:
            if console:
                console.clear()
                console.print(Panel("[bold magenta]🔍 Test Runner Console[/bold magenta]", border_style="magenta"))

                table = Table(show_header=False, box=None)
                table.add_column("#", style="cyan", justify="right")
                table.add_column("Action", style="white")
                table.add_row("1", "📚 Run all tests")
                table.add_row("2", "🗂️ Run test file pattern")
                table.add_row("3", "🧪 Run Alert Core tests")
                table.add_row("4", "🎯 Pick tests to run")
                table.add_row("5", "❌ Exit")
                console.print(table)
                choice = console.input("Choose > ").strip()
            else:
                os.system("cls" if os.name == "nt" else "clear")
                print("\n=== 🔍 Test Runner Console ===")
                print("1) 📚 Run all tests")
                print("2) 🗂️ Run test file pattern")
                print("3) 🧪 Run Alert Core tests")
                print("4) 🎯 Pick tests to run")
                print("5) ❌ Exit")
                choice = input("Choose > ").strip()

            if choice == "1":
                self.run_glob()
            elif choice == "2":
                pattern_prompt = "Pattern (e.g., tests/test_*.py): "
                pattern = console.input(pattern_prompt).strip() if console else input(pattern_prompt).strip()
                self.run_glob(pattern)
            elif choice == "3":
                self.test_alert_core()
            elif choice == "4":
                self.pick_and_run_tests()
            elif choice == "5":
                break
            else:
                if console:
                    console.print("[red]Invalid choice. Try again.[/red]")
                else:
                    print("Invalid choice. Try again.")
                continue

            if console:
                console.input("\n[grey]Press ENTER to return...[/grey]")
            else:
                input("\nPress ENTER to return...")

