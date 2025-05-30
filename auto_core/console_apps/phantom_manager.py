# =============================================================================
# 🦄 PhantomManager
# -----------------------------------------------------------------------------
# Playwright-based automation helper for the Phantom browser extension.  This
# module launches a Chromium browser with Phantom loaded, provides utilities for
# unlocking the wallet, approving transactions and handling onboarding flows.
# =============================================================================

import logging
import os
from typing import List, Optional
from playwright.sync_api import sync_playwright, Error
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

if not logger.handlers:
    fh = logging.FileHandler("phantom_manager.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(_formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(_formatter)
    logger.addHandler(ch)


class PhantomManager:
    """Manage Phantom wallet browser automation via Playwright."""

    def __init__(self, extension_path: str, user_data_dir: str = "playwright-data", headless: bool = False) -> None:
        self.extension_path = extension_path
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.browser_context = None
        self.playwright = None
        self.page = None
        self.popup = None
        self.phantom_id = None

        if self.extension_path.lower().endswith(".crx"):
            logger.warning(
                "Provided extension_path is a .crx file. Please extract it to an unpacked folder."
            )

    # ------------------------------------------------------------------
    def launch_browser(self) -> None:
        """Launch a Chromium browser with the Phantom extension loaded."""
        logger.debug("Launching browser with Phantom extension from %s", self.extension_path)
        self.playwright = sync_playwright().start()
        try:
            self.browser_context = self.playwright.chromium.launch_persistent_context(
                self.user_data_dir,
                headless=self.headless,
                channel="chrome",
                args=[
                    f"--disable-extensions-except={self.extension_path}",
                    f"--load-extension={self.extension_path}",
                    "--window-size=1280,720",
                    "--start-maximized",
                ],
            )
        except Error as exc:
            logger.error("Error launching browser context: %s", exc)
            raise

        self.page = self.browser_context.new_page()
        self.page.on("console", lambda msg: logger.debug("PAGE CONSOLE: %s", msg.text))

        if os.path.exists(self.user_data_dir) and os.listdir(self.user_data_dir):
            timeout_value = 2500
            logger.debug(
                "Existing user data detected. Using shorter service worker timeout: %d ms",
                timeout_value,
            )
        else:
            timeout_value = 30000
            logger.debug(
                "Fresh user data. Using longer service worker timeout: %d ms", timeout_value
            )

        logger.debug(
            "Waiting for service worker to register Phantom extension (timeout %d ms)...",
            timeout_value,
        )
        try:
            sw = self.browser_context.wait_for_event("serviceworker", timeout=timeout_value)
            self.phantom_id = sw.url.split("/")[2]
            logger.debug("Phantom extension loaded with ID: %s", self.phantom_id)
        except Error as exc:
            logger.error("Service worker not registered within timeout: %s", exc)
            for idx, pg in enumerate(self.browser_context.pages):
                logger.debug("Open page %s: %s", idx, pg.url)
            fallback_id = "bfnaelmomeimhlpmgjnjophhpkkoljpa"
            logger.debug("Assuming Phantom extension ID as fallback: %s", fallback_id)
            self.phantom_id = fallback_id

    # ------------------------------------------------------------------
    def open_phantom_popup(self):
        """Open the Phantom popup UI."""
        if not self.phantom_id:
            logger.error("Phantom extension not loaded. Call launch_browser() first.")
            raise RuntimeError("Phantom extension not loaded. Call launch_browser() first.")
        logger.debug("Opening Phantom popup UI...")
        self.popup = self.browser_context.new_page()
        self.popup.on("console", lambda msg: logger.debug("POPUP CONSOLE: %s", msg.text))
        try:
            self.popup.goto(f"chrome-extension://{self.phantom_id}/popup.html", timeout=10000)
            self.popup.wait_for_load_state()
            logger.debug("Phantom popup UI loaded. URL: %s", self.popup.url)
        except Error as exc:
            logger.error("Error loading Phantom popup: %s", exc)
            raise
        return self.popup

    # ------------------------------------------------------------------
    def dismiss_post_unlock_dialog(self):
        """Dismiss the 'Click this dialog to continue' overlay if present."""
        overlay_selector = "text=Click this dialog to continue"
        try:
            self.popup.wait_for_selector(overlay_selector, timeout=3000)
            self.popup.click(overlay_selector)
            logger.debug("Dismissed the 'Click this dialog to continue' overlay.")
            self.popup.wait_for_timeout(1000)
        except Error as exc:
            logger.debug("No post-unlock dialog overlay found or timed out: %s", exc)

    # ------------------------------------------------------------------
    def approve_transaction(
        self,
        transaction_trigger_selector: str,
        confirm_selectors: Optional[List[str]] = None,
        trigger_timeout: int = 10000,
        confirm_timeout: int = 5000,
    ) -> None:
        """Trigger a transaction in the dApp and approve it in Phantom."""
        logger.debug("Triggering transaction with selector: %s", transaction_trigger_selector)
        try:
            self.page.click(transaction_trigger_selector, timeout=trigger_timeout)
        except Error as exc:
            logger.error("Error triggering transaction: %s", exc)
            raise

        if not self.popup or self.popup.is_closed():
            logger.debug("Phantom popup not open; opening popup for transaction approval.")
            self.open_phantom_popup()
        else:
            logger.debug("Bringing Phantom popup to front and reloading to update state.")
            self.popup.bring_to_front()
            self.popup.reload()

        if confirm_selectors is None:
            confirm_selectors = [
                "button[data-testid='primary-button']:has-text('Confirm Transaction')",
                "button[data-testid='primary-button']:has-text('Confirm')",
                "text=Confirm",
            ]

        success = False
        for selector in confirm_selectors:
            try:
                logger.debug("Waiting for confirm button with selector: %s", selector)
                self.popup.wait_for_selector(selector, timeout=confirm_timeout)
                logger.debug("Clicking confirm button with selector: %s", selector)
                self.popup.click(selector, timeout=confirm_timeout)
                success = True
                break
            except Error as exc:
                logger.warning("Confirm button not found with selector %s: %s", selector, exc)
                continue

        if not success:
            logger.error("Failed to click any confirm button with provided selectors.")
            raise RuntimeError("Transaction approval failed: No confirm button found.")

        logger.debug("Transaction approved (Confirm clicked).")

    # ------------------------------------------------------------------
    def handle_onboarding(self) -> None:
        logger.debug("Handling Phantom onboarding...")
        try:
            self.popup.wait_for_selector("text=I already have a wallet", timeout=15000)
            self.popup.click("text=I already have a wallet", timeout=10000)
            logger.debug("Selected 'I already have a wallet' in onboarding.")
        except Error as exc:
            if "Target page, context or browser has been closed" in str(exc):
                logger.warning("Phantom onboarding popup was closed. Skipping onboarding handling.")
            else:
                logger.warning("Onboarding UI not detected or already handled: %s", exc)

    # ------------------------------------------------------------------
    def handle_wallet_selection(self, wallet_selector: str = "text=Use this wallet") -> None:
        logger.debug("Handling wallet selection with selector: %s", wallet_selector)
        try:
            self.popup.wait_for_selector(wallet_selector, timeout=15000)
            self.popup.click(wallet_selector, timeout=10000)
            logger.debug("Wallet selection completed.")
        except Error as exc:
            logger.warning("Wallet selection UI not detected or already handled: %s", exc)

    # ------------------------------------------------------------------
    def connect_wallet(
        self,
        dapp_url: str,
        dapp_connect_selector: str = "css=span.text-v2-primary",
        popup_connect_selector: str = "text=Connect",
        wallet_selection_selector: str = "text=Use this wallet",
        dapp_connected_selector: str = "text=Connected",
        phantom_password: Optional[str] = None,
    ) -> None:
        logger.debug("Navigating to dApp: %s", dapp_url)
        try:
            self.page.goto(dapp_url, timeout=15000)
            logger.debug("dApp page loaded. Current URL: %s", self.page.url)
        except Error as exc:
            logger.error("Error navigating to dApp: %s", exc)
            raise

        logger.debug("Checking if wallet is already connected using selector: %s", dapp_connected_selector)
        try:
            self.page.wait_for_selector(dapp_connected_selector, timeout=5000)
            logger.debug("Wallet already connected on dApp. Skipping connect flow.")
            return
        except Error:
            logger.debug("Wallet not connected; proceeding with connect flow.")

        logger.debug("Waiting for dApp connect button with selector: %s", dapp_connect_selector)
        try:
            self.page.wait_for_selector(dapp_connect_selector, timeout=15000)
            logger.debug("Clicking dApp connect button with selector: %s", dapp_connect_selector)
            self.page.click(dapp_connect_selector, timeout=10000)
        except Error as exc:
            logger.error("Error clicking dApp connect button: %s", exc)
            raise

        logger.debug("Opening Phantom popup to approve wallet connection.")
        popup = self.open_phantom_popup()
        if phantom_password:
            self.unlock_phantom(phantom_password)
        else:
            logger.warning(
                "No Phantom password provided. Please disable auto-lock in Phantom settings as a backup."
            )

        self.handle_onboarding()
        if popup.is_closed():
            logger.debug("Phantom popup closed after onboarding, reopening.")
            popup = self.open_phantom_popup()

        success = False
        attempts = 0
        max_attempts = 2
        while not success and attempts < max_attempts:
            try:
                popup.wait_for_selector(popup_connect_selector, timeout=10000)
                logger.debug(
                    "Clicking Phantom popup connect button with selector: %s", popup_connect_selector
                )
                popup.click(popup_connect_selector, timeout=10000)
                success = True
            except Error as exc:
                if popup.is_closed():
                    logger.warning("Phantom popup closed unexpectedly; assuming connection is approved.")
                    success = True
                else:
                    attempts += 1
                    logger.error(
                        "Error in Phantom connect button flow (attempt %d): %s", attempts, exc
                    )
                    logger.debug("Reopening Phantom popup and retrying...")
                    popup = self.open_phantom_popup()
        if not success:
            logger.warning(
                "Phantom connect button not found after multiple attempts; assuming connection is approved."
            )

        self.handle_wallet_selection(wallet_selector=wallet_selection_selector)
        logger.debug(
            "Waiting for dApp to confirm wallet association using selector: %s", dapp_connected_selector
        )
        try:
            self.page.wait_for_selector(dapp_connected_selector, timeout=10000)
            logger.debug("DApp wallet association confirmed.")
        except Error as exc:
            logger.warning("DApp wallet association not confirmed: %s", exc)

    # ------------------------------------------------------------------
    def capture_order_payload(self, url_keyword: str, timeout: int = 10000):
        """Capture payload for a request whose URL contains ``url_keyword``."""
        logger.debug("Waiting for network request with keyword: %s", url_keyword)
        try:
            request = self.page.wait_for_event(
                "requestfinished",
                predicate=lambda req: url_keyword in req.url,
                timeout=timeout,
            )
            try:
                payload = request.post_data_json()
            except Exception:
                payload = request.post_data()
            logger.debug("Captured order payload: %s", payload)
            return payload
        except Error as exc:
            logger.error("Error capturing order payload: %s", exc)
            raise

    # ------------------------------------------------------------------
    def unlock_phantom(self, phantom_password: str) -> None:
        """Unlock the Phantom wallet using the given password."""
        logger.debug("Unlocking Phantom: selecting password input field.")
        if self.popup is None or self.popup.is_closed():
            logger.debug("Phantom popup not open; opening popup for unlocking.")
            self.open_phantom_popup()
        try:
            self.popup.wait_for_selector(
                "input[data-testid='unlock-form-password-input']", timeout=5000
            )
            logger.debug("Phantom password input detected. Filling in password.")
            self.popup.fill(
                "input[data-testid='unlock-form-password-input']", phantom_password, timeout=2000
            )
            logger.debug("Password entered; now clicking the unlock button.")
            self.popup.click(
                "button[data-testid='unlock-form-submit-button']", timeout=5000
            )
            logger.debug("Clicked unlock button. Waiting briefly for unlock to complete...")
            self.popup.wait_for_timeout(2000)
            self.dismiss_post_unlock_dialog()
        except Error as exc:
            logger.error("Error unlocking Phantom: %s", exc)
            raise

    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close the browser context and Playwright instance."""
        logger.debug("Closing browser context.")
        if self.browser_context:
            self.browser_context.close()
        if self.playwright:
            self.playwright.stop()
        logger.debug("Browser closed.")
