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
    await page.goto("https://x.com/i/flow/login", wait_until="networkidle")

    # Enter username / email
    print("[2/4] Entering username …")
    username_input = page.get_by_label("Phone, email, or username")
    await username_input.wait_for(state="visible", timeout=15_000)
    await username_input.fill(username)
    await page.get_by_role("button", name="Next").click()

    # X sometimes asks for an email/phone verification step
    try:
        verify_input = page.get_by_label("Phone or email")
        await verify_input.wait_for(state="visible", timeout=5_000)
        print("    (verification prompt detected – entering username again)")
        await verify_input.fill(username)
        await page.get_by_role("button", name="Next").click()
    except PlaywrightTimeoutError:
        pass  # no extra verification needed

    # Enter password
    print("[3/4] Entering password …")
    password_input = page.get_by_label("Password", exact=True)
    await password_input.wait_for(state="visible", timeout=10_000)
    await password_input.fill(password)
    await page.get_by_role("button", name="Log in").click()

    # Wait for home feed to confirm successful login
    await page.wait_for_url("https://x.com/home", timeout=20_000)
    print("      ✓ Logged in successfully!")


async def create_post(page, text: str) -> None:
    """Compose and submit a post on X.com."""
    print("[4/4] Creating post …")

    # Click the compose box (the "What is happening?!" placeholder)
    compose_box = page.get_by_role("textbox", name="Post text")
    await compose_box.wait_for(state="visible", timeout=15_000)
    await compose_box.click()
    await compose_box.fill(text)

    # Click the "Post" button
    post_button = page.get_by_test_id("tweetButtonInline")
    await post_button.wait_for(state="visible", timeout=10_000)
    await post_button.click()

    # Wait briefly for the post to be submitted
    await page.wait_for_timeout(3_000)
    print(f"      ✓ Post submitted: "{text}"")


async def main() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,          # set True for background / CI runs
            slow_mo=150,             # slight delay so actions look natural
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="en-US",
        )
        page = await context.new_page()

        try:
            await login(page, USERNAME, PASSWORD)
            await create_post(page, POST_TEXT)
        except PlaywrightTimeoutError as e:
            print(f"\n✗ Timeout error: {e}")
            print("  → Try running with headless=False to debug, or check your credentials.")
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
        finally:
            await page.wait_for_timeout(2_000)   # let you see the result
            await browser.close()
            print("Browser closed. Done!")


if __name__ == "__main__":
    asyncio.run(main())
