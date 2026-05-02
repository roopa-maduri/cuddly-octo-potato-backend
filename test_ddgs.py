from duckduckgo_search import DDGS

def test():
    results = DDGS().text("maggi price Zepto India", max_results=3)
    print("Results:", list(results))

if __name__ == "__main__":
    test()
