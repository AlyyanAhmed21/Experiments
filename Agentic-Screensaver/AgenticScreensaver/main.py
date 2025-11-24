from agent.core import Agent
import os
import google.generativeai as genai
from config import GEMINI_API_KEY

def check_api():
    key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
    if not key:
        print("⚠️  WARNING: GEMINI_API_KEY not found in environment variables or config.")
        print("   The agent will run in MOCK mode (repetitive visuals).")
        return False
    
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-flash-latest')
        # Simple generation to test auth
        response = model.generate_content("Test")
        print("✅ API Connection Successful!")
        return True
    except Exception as e:
        print(f"❌ API Connection Failed: {e}")
        print("   The agent will run in MOCK mode.")
        return False

if __name__ == "__main__":
    check_api()
    agent = Agent()
    agent.run()
