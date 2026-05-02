import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://blinkit.com/s/?q=maggi')
        await page.wait_for_timeout(5000)
        html = await page.content()
        print(html[:2000])
        print("...")
        
        # also print all text that has ₹ in it
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text()
        import re
        prices = re.findall(r'₹\s*(\d+)', text)
        print("Prices found:", prices)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
