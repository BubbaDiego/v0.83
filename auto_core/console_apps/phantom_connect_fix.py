from playwright.sync_api import Page
import logging

logger = logging.getLogger(__name__)

def find_and_click_connect_button(page: Page) -> None:
    # 🎯 STEP 1: Prioritized Connect buttons by UI importance
    prioritized_indices = [15, 24, 3]  # Main, Fallback, Nav
    buttons = page.locator("button")
    for i in prioritized_indices:
        try:
            btn = buttons.nth(i)
            if btn.is_visible():
                btn.click()
                logger.debug(f"✅ Clicked Connect button index [{i}] (prioritized)")
                page.wait_for_timeout(500)
                break
        except Exception as e:
            logger.debug(f"❌ Failed to click Connect button index [{i}]: {e}")

    # 🧩 STEP 2: Expand wallet list
    try:
        if page.locator("text=View More Wallets").is_visible():
            page.click("text=View More Wallets")
            logger.debug("Expanded wallet list to show Phantom.")
            page.wait_for_timeout(500)
    except Exception as e:
        logger.debug(f"Wallet expand step skipped: {e}")

    # 🧠 STEP 3: Select Phantom
    selectors = [
        "text=Phantom",
        "button:has-text('Phantom')",
        "xpath=//button[contains(., 'Phantom')]",
        "xpath=//span[contains(text(), 'Phantom')]/ancestor::button"
    ]
    for sel in selectors:
        try:
            locator = page.locator(sel)
            if locator.is_visible():
                locator.click()
                logger.debug(f"Clicked Phantom with selector: {sel}")
                return
        except Exception as e:
            logger.debug(f"Phantom selector failed: {sel} → {e}")
            continue

    raise RuntimeError("❌ Failed to find and click Phantom wallet button.")
