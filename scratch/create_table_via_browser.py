"""
create_table_via_browser.py
Opens Supabase SQL editor in a headed browser so the user can see what's happening,
pastes the SQL, and runs it to create the 'test' table.
"""
import asyncio, sys, io

if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from playwright.async_api import async_playwright

SQL = """CREATE TABLE IF NOT EXISTS test (
    id TEXT PRIMARY KEY,
    token_id TEXT,
    token_label TEXT,
    guild_id TEXT,
    guild_name TEXT,
    channel_id TEXT,
    channel_name TEXT,
    writable BOOLEAN,
    text_allowed BOOLEAN,
    link_allowed BOOLEAN,
    last_scan TIMESTAMPTZ DEFAULT NOW(),
    scan_reason TEXT
);"""

PROJECT_REF = "cwputkmuqgpxydfxsrnm"
SQL_EDITOR_URL = f"https://supabase.com/dashboard/project/{PROJECT_REF}/sql/new"

async def run():
    print(f"Opening Supabase SQL Editor: {SQL_EDITOR_URL}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        print("Navigating to Supabase SQL Editor...")
        await page.goto(SQL_EDITOR_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        print(f"Current URL: {page.url}")

        # Check if we're on a login page
        if "sign-in" in page.url or "login" in page.url:
            print("Need to log in first. Waiting for login...")
            # Wait up to 120s for user to log in
            await page.wait_for_url(f"**/project/{PROJECT_REF}/**", timeout=120000)
            print("Logged in! Navigating to SQL Editor...")
            await page.goto(SQL_EDITOR_URL, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)

        print(f"On page: {page.url}")

        # Try to find the SQL editor textarea / CodeMirror editor
        print("Looking for SQL editor input...")
        await page.wait_for_timeout(4000)

        # Supabase SQL editor uses CodeMirror - click the editor area and type
        editor = await page.query_selector(".cm-content")
        if not editor:
            editor = await page.query_selector(".view-line")
        if not editor:
            editor = await page.query_selector("[data-testid='sql-editor']")
        if not editor:
            # Try clicking the general editor area
            editor = await page.query_selector(".cm-editor")

        if editor:
            print("Found editor. Clicking and entering SQL...")
            await editor.click()
            await page.wait_for_timeout(500)
            # Select all existing content and replace
            await page.keyboard.press("Control+a")
            await page.wait_for_timeout(300)
            await page.keyboard.type(SQL)
            await page.wait_for_timeout(1000)
            print("SQL entered. Looking for Run button...")

            # Find Run button
            run_btn = await page.query_selector("button:has-text('Run')")
            if not run_btn:
                run_btn = await page.query_selector("[data-testid='run-query-button']")
            if not run_btn:
                # Try keyboard shortcut Ctrl+Enter
                print("Run button not found, trying Ctrl+Enter...")
                await page.keyboard.press("Control+Enter")
            else:
                print("Clicking Run button...")
                await run_btn.click()

            await page.wait_for_timeout(3000)
            print("SQL executed! Checking for success message...")

            # Look for success/result indicators
            success = await page.query_selector(".text-success, [data-status='success'], .bg-green")
            if success:
                print("SUCCESS: Table created successfully!")
            else:
                print("Check browser window to confirm table was created.")

            await page.wait_for_timeout(5000)

        else:
            print("Could not find SQL editor automatically.")
            print(f"Please manually paste this SQL in the editor at: {SQL_EDITOR_URL}")
            print("\nSQL to run:")
            print(SQL)
            print("\nBrowser window is open. Press Enter here when done.")
            await page.wait_for_timeout(60000)

        await browser.close()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(run())
