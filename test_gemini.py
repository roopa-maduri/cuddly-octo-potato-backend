import google.generativeai as genai
import json

def test():
    api_key = "AIzaSyBWINXh7y1nXAthFXSMXZeHJwRqPPzwccA"
    genai.configure(api_key=api_key)
    
    item = "maggi 15 rupees"
    
    prompt = f"""
    You are a grocery price estimator for the Indian market.
    The user is searching for the item: "{item}".
    Estimate the realistic current price in INR for this exact item on 4 delivery platforms: Swiggy Instamart, Zepto, Blinkit, and Toing!.
    Return ONLY a JSON array of exactly 4 objects matching this schema:
    [
        {{"platform": "Swiggy Instamart", "original_price": 50, "discounted_price": 45, "delivery_time": "15 mins"}},
        {{"platform": "Zepto", "original_price": 52, "discounted_price": 46, "delivery_time": "10 mins"}},
        {{"platform": "Blinkit", "original_price": 49, "discounted_price": 48, "delivery_time": "12 mins"}},
        {{"platform": "Toing!", "original_price": 50, "discounted_price": 35, "delivery_time": "20 mins"}}
    ]
    Make the prices realistic for "{item}" in India right now. Toing! is known to be the most affordable.
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
        response = model.generate_content(prompt)
        print("Response Text:", response.text)
        data = json.loads(response.text)
        print("Parsed JSON:", data)
    except Exception as e:
        print("Error:", repr(e))

if __name__ == "__main__":
    test()
