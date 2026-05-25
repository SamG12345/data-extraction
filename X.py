"""
X.com (Twitter) Auto-Poster using Playwright
Usage:
    pip install playwright
    playwright install chromium
    python x_post.py
"""

import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ── Configuration ────────────────────────────────────────────────────────────
USERNAME  = "your_username_or_email"   # ← replace
PASSWORD  = "your_password"            # ← replace
POST_TEXT = "Hello from Playwright! 🤖 #automation"
# ─────────────────────────────────────────────────────────────────────────────


async def login(page, username: str, password: str) -> None:
    """Log in to X.com."""
    print("[1/4] Navigating to login page …")
    await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=60_000)

    # Wait for ANY input to appear (X renders inputs dynamically)
    print("[2/4] Entering username …")
    await page.wait_for_selector("input", state="visible", timeout=30_000)
    await page.wait_for_timeout(1_500)   # let animations settle

    # Fill the first visible input (always the username field on this page)
    await page.locator("input:visible").first.fill(username)
    await page.wait_for_timeout(500)

    # Click Next
    await page.locator("button:has-text('Next')").click()
    await page.wait_for_timeout(2_000)

    # X sometimes shows an extra verification step (phone/email)
    try:
        extra = page.locator("input:visible").first
        await extra.wait_for(state="visible", timeout=4_000)
        label_text = await page.locator("label:visible").first.inner_text()
        if "phone" in label_text.lower() or "email" in label_text.lower():
            print("    (verification prompt detected – entering username again)")
            await extra.fill(username)
            await page.locator("button:has-text('Next')").click()
            await page.wait_for_timeout(2_000)
    except PlaywrightTimeoutError:
        pass

    # Enter password
    print("[3/4] Entering password …")
    await page.wait_for_selector("input[type='password']", state="visible", timeout=15_000)
    await page.locator("input[type='password']").fill(password)
    await page.wait_for_timeout(500)

    # Click Log in
    await page.locator("button:has-text('Log in')").click()

    # Confirm redirect to home
    await page.wait_for_url("**/home", timeout=30_000)
    await page.wait_for_timeout(2_000)
    print("      ✓ Logged in successfully!")


async def create_post(page, text: str) -> None:
    """Compose and submit a post on X.com."""
    print("[4/4] Creating post …")

    # Wait for the compose area
    await page.wait_for_selector("[data-testid='tweetTextarea_0']", state="visible", timeout=20_000)
    await page.locator("[data-testid='tweetTextarea_0']").click()
    await page.wait_for_timeout(500)
    await page.keyboard.type(text, delay=30)   # type naturally to avoid paste detection
    await page.wait_for_timeout(1_000)

    # Submit the post
    post_btn = page.locator("[data-testid='tweetButtonInline']")
    await post_btn.wait_for(state="visible", timeout=10_000)
    await post_btn.click()
    await page.wait_for_timeout(3_000)
    print(f'      ✓ Post submitted: "{text}"')


async def main() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            slow_mo=80,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        try:
            await login(page, USERNAME, PASSWORD)
            await create_post(page, POST_TEXT)
        except PlaywrightTimeoutError as e:
            print(f"\n✗ Timeout error: {e}")
            print("  → The page may be loading slowly. Try increasing wait times or check your connection.")
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
        finally:
            await page.wait_for_timeout(2_000)
            await browser.close()
            print("Browser closed. Done!")


if __name__ == "__main__":
    asyncio.run(main())
