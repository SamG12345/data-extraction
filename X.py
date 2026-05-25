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


async def click_next_button(page) -> None:
    """Click the Next/Continue button — tries several strategies."""
    # Strategy 1: data-testid (most stable)
    for testid in ("LoginForm_Login_Button", "ocfEnterTextNextButton", "next_link"):
        try:
            btn = page.locator(f"[data-testid='{testid}']")
            await btn.wait_for(state="visible", timeout=3_000)
            await btn.click()
            return
        except PlaywrightTimeoutError:
            pass

    # Strategy 2: any button whose text contains 'next' or 'continue' (case-insensitive)
    btn = page.locator("button").filter(has_text="Next")
    count = await btn.count()
    if count:
        await btn.first.click()
        return

    # Strategy 3: press Enter on the current input
    await page.keyboard.press("Enter")


async def login(page, username: str, password: str) -> None:
    """Log in to X.com."""
    print("[1/4] Navigating to login page …")
    await page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=60_000)

    # Wait until at least one input is visible
    await page.wait_for_selector("input", state="visible", timeout=30_000)
    await page.wait_for_timeout(2_000)   # let JS finish rendering

    # Step 1 – username
    print("[2/4] Entering username …")
    inp = page.locator("input:visible").first
    await inp.click()
    await inp.fill(username)
    await page.wait_for_timeout(600)
    await click_next_button(page)
    await page.wait_for_timeout(2_500)

    # Step 1b – optional extra verification (phone / email)
    try:
        label = await page.locator("label:visible").first.inner_text(timeout=3_000)
        if any(w in label.lower() for w in ("phone", "email", "verify")):
            print("    (extra verification prompt – re-entering username)")
            extra = page.locator("input:visible").first
            await extra.fill(username)
            await page.wait_for_timeout(500)
            await click_next_button(page)
            await page.wait_for_timeout(2_500)
    except Exception:
        pass

    # Step 2 – password
    print("[3/4] Entering password …")
    await page.wait_for_selector("input[type='password']", state="visible", timeout=20_000)
    pwd = page.locator("input[type='password']").first
    await pwd.click()
    await pwd.fill(password)
    await page.wait_for_timeout(600)

    # Click "Log in"
    logged_in = False
    for testid in ("LoginForm_Login_Button", "login-button"):
        try:
            btn = page.locator(f"[data-testid='{testid}']")
            await btn.wait_for(state="visible", timeout=3_000)
            await btn.click()
            logged_in = True
            break
        except PlaywrightTimeoutError:
            pass
    if not logged_in:
        btn = page.locator("button").filter(has_text="Log in")
        if await btn.count():
            await btn.first.click()
        else:
            await page.keyboard.press("Enter")

    await page.wait_for_url("**/home", timeout=30_000)
    await page.wait_for_timeout(2_000)
    print("      ✓ Logged in successfully!")


async def create_post(page, text: str) -> None:
    """Compose and submit a post on X.com."""
    print("[4/4] Creating post …")

    await page.wait_for_selector("[data-testid='tweetTextarea_0']", state="visible", timeout=20_000)
    box = page.locator("[data-testid='tweetTextarea_0']")
    await box.click()
    await page.wait_for_timeout(500)
    await page.keyboard.type(text, delay=40)
    await page.wait_for_timeout(1_000)

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
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
        finally:
            await page.wait_for_timeout(2_000)
            await browser.close()
            print("Browser closed. Done!")


if __name__ == "__main__":
    asyncio.run(main())
