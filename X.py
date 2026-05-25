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
    # Use 'domcontentloaded' – X.com never fully reaches 'networkidle'
    await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=60_000)
    # Give React/JS time to render the form
    await page.wait_for_timeout(3_000)

    # Enter username / email — try multiple selectors for resilience
    print("[2/4] Entering username …")
    try:
        username_input = page.get_by_label("Phone, email, or username")
        await username_input.wait_for(state="visible", timeout=20_000)
    except PlaywrightTimeoutError:
        # Fallback: grab the first visible text input on the page
        username_input = page.locator("input[autocomplete='username'], input[name='text']").first
        await username_input.wait_for(state="visible", timeout=10_000)

    await username_input.fill(username)
    await page.get_by_role("button", name="Next").click()
    await page.wait_for_timeout(2_000)

    # X sometimes asks for an email/phone verification step
    try:
        verify_input = page.get_by_label("Phone or email")
        await verify_input.wait_for(state="visible", timeout=5_000)
        print("    (verification prompt detected – entering username again)")
        await verify_input.fill(username)
        await page.get_by_role("button", name="Next").click()
        await page.wait_for_timeout(2_000)
    except PlaywrightTimeoutError:
        pass  # no extra verification needed

    # Enter password
    print("[3/4] Entering password …")
    try:
        password_input = page.get_by_label("Password", exact=True)
        await password_input.wait_for(state="visible", timeout=15_000)
    except PlaywrightTimeoutError:
        password_input = page.locator("input[type='password']").first
        await password_input.wait_for(state="visible", timeout=10_000)

    await password_input.fill(password)
    await page.get_by_role("button", name="Log in").click()

    # Wait for home feed to confirm successful login
    await page.wait_for_url("**/home", timeout=30_000)
    await page.wait_for_timeout(2_000)
    print("      ✓ Logged in successfully!")


async def create_post(page, text: str) -> None:
    """Compose and submit a post on X.com."""
    print("[4/4] Creating post …")

    # Click the compose box — try multiple selectors
    try:
        compose_box = page.get_by_role("textbox", name="Post text")
        await compose_box.wait_for(state="visible", timeout=15_000)
    except PlaywrightTimeoutError:
        compose_box = page.locator("[data-testid='tweetTextarea_0']").first
        await compose_box.wait_for(state="visible", timeout=10_000)

    await compose_box.click()
    await compose_box.fill(text)
    await page.wait_for_timeout(1_000)

    # Click the "Post" button
    try:
        post_button = page.get_by_test_id("tweetButtonInline")
        await post_button.wait_for(state="visible", timeout=10_000)
    except PlaywrightTimeoutError:
        post_button = page.locator("[data-testid='tweetButton']").first
        await post_button.wait_for(state="visible", timeout=10_000)

    await post_button.click()
    await page.wait_for_timeout(3_000)
    print(f'      ✓ Post submitted: "{text}"')


async def main() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,   # set True for background / CI runs
            slow_mo=100,      # slight delay so actions look natural
            args=["--disable-blink-features=AutomationControlled"],  # reduce bot detection
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
            print("  → Check your internet connection or try again (X.com may be slow).")
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
        finally:
            await page.wait_for_timeout(2_000)
            await browser.close()
            print("Browser closed. Done!")


if __name__ == "__main__":
    asyncio.run(main())
