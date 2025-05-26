"""Automated collateral management via the Jupiter UI."""

from playwright.sync_api import sync_playwright

from . import phantom_workflow as pwf


class AutoCore:
    """High level workflows using Playwright and Phantom."""

    def __init__(self, phantom_path: str, profile_dir: str, headless: bool = False) -> None:
        self.phantom_path = phantom_path
        self.profile_dir = profile_dir
        self.headless = headless

    # ------------------------------------------------------------------
    def _launch_context(self):
        pw = sync_playwright().start()
        context = pw.chromium.launch_persistent_context(
            self.profile_dir,
            channel="chromium",
            headless=self.headless,
            args=[
                f"--disable-extensions-except={self.phantom_path}",
                f"--load-extension={self.phantom_path}",
            ],
        )
        page = context.new_page()
        page.goto("https://jup.ag/perpetuals")
        return pw, context, page

    def _close(self, pw, context):
        context.close()
        pw.stop()

    # ------------------------------------------------------------------
    def deposit_collateral(self, amount: float) -> None:
        """Automate collateral deposit via the UI."""
        pw, ctx, page = self._launch_context()
        try:
            pwf.connect_wallet(page)
            page.fill("input[type=number]", str(amount))
            page.click("button:has-text('Deposit')")
            pwf.approve_popup(page)
            pwf.confirm_transaction(page)
        finally:
            self._close(pw, ctx)

    def withdraw_collateral(self, amount: float) -> None:
        """Automate collateral withdrawal via the UI."""
        pw, ctx, page = self._launch_context()
        try:
            pwf.connect_wallet(page)
            page.fill("input[type=number]", str(amount))
            page.click("button:has-text('Withdraw')")
            pwf.approve_popup(page)
            pwf.confirm_transaction(page)
        finally:
            self._close(pw, ctx)

