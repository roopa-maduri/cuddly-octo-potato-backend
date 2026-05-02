import asyncio
import logging
from scrapers import perform_live_search

# Setup logging to see the error
logging.basicConfig(level=logging.ERROR)

async def test_scrapers():
    print("Running perform_live_search...")
    try:
        results = await perform_live_search("maggi 15 rupees")
        print("Results length:", len(results))
        for r in results:
            print(r)
    except Exception as e:
        print("Crash:", repr(e))

if __name__ == "__main__":
    asyncio.run(test_scrapers())
