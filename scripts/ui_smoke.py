import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.on('console', lambda msg: print('[CONSOLE]', msg.type, msg.text))

        await page.goto('http://localhost:5173', wait_until='networkidle')
        await page.wait_for_selector('input[type="text"]:not([disabled])', timeout=8000)
        await page.fill('input[type="text"]', 'nearby cafes')
        await page.click('button[type="submit"]')

        try:
            await page.wait_for_selector('text=Nearby Cafes', timeout=10000)
        except Exception:
            pass

        await page.wait_for_timeout(4000)
        body = await page.inner_text('body')
        print('---BODY---')
        print(body[:3000])
        await browser.close()

asyncio.run(main())
