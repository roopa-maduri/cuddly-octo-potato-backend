import asyncio
from scrapers import perform_live_search

async def main():
    res = await perform_live_search("maggi 15 rupees", "500001", "INR")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
