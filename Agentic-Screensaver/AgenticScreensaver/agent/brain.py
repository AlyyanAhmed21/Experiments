import google.generativeai as genai
import json
import os
import random

class Brain:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.mock_mode = not self.api_key
        
        if not self.mock_mode:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')

    def decide(self, sensor_data, recent_history):
        """
        Decides on the next visual theme and poetry based on inputs.
        """
        if self.mock_mode:
            return self._mock_decision(sensor_data)

        prompt = self._construct_prompt(sensor_data, recent_history)
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response (handling potential markdown wrapping)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
        except Exception as e:
            print(f"LLM Error: {e}. Falling back to mock.")
            return self._mock_decision(sensor_data)

    def _construct_prompt(self, data, history):
        return f"""
        You are the creative spirit of a computer. 
        Current System State:
        - CPU Load: {data.get('cpu')}%
        - RAM Usage: {data.get('ram')}%
        - Time: {data.get('period')} ({data.get('hour')}:00)
        
        Recent Themes: {history}

        Based on this, generate a JSON object with:
        1. "theme": A short evocative name for the visual style.
        2. "sky_colors": A list of 2 RGB color tuples for a vertical gradient (top, bottom). e.g. [[10,10,50], [200,100,50]].
        3. "weather": One of ["clear", "rain", "snow", "fireflies", "fog", "stars"].
        4. "poetry": A famous, inspiring quote (max 20 words) that fits the mood. Include author if known.
        5. "font": One of ["DancingScript", "Merienda", "PlayfairDisplay"].
        6. "wind_speed": A float 0.0-2.0 (speed of particles).
        7. "complexity": A float 0.0-1.0.

        If CPU is high, maybe stormy/rainy. If night, maybe stars/fireflies. Be creative and aesthetic.
        Output ONLY valid JSON.
        """

    def _mock_decision(self, data):
        """Fallback if no API key is present."""
        cpu = data.get('cpu', 0)
        is_high_load = cpu > 50
        
        # Real quotes for mock mode
        if is_high_load:
            themes = [
                ("Digital Storm", "rain", "The best way out is always through. - Robert Frost", "PlayfairDisplay"),
                ("Overclocked", "snow", "Chaos is a ladder. - George R.R. Martin", "PlayfairDisplay"),
                ("Red Alert", "fireflies", "Do not go gentle into that good night. - Dylan Thomas", "Merienda")
            ]
            t = random.choice(themes)
            return {
                "theme": t[0],
                "sky_colors": [[50, 0, 0], [20, 0, 0]],
                "weather": t[1],
                "poetry": t[2],
                "font": t[3],
                "wind_speed": 1.5,
                "complexity": 0.9
            }
        else:
            themes = [
                ("Deep Sleep", "stars", "We are such stuff as dreams are made on. - Shakespeare", "DancingScript"),
                ("Azure Sky", "clear", "Simplicity is the ultimate sophistication. - Leonardo da Vinci", "PlayfairDisplay"),
                ("Night Watch", "fireflies", "Look at the stars. Look how they shine for you. - Coldplay", "DancingScript"),
                ("Foggy Morning", "fog", "Life is really simple, but we insist on making it complicated. - Confucius", "Merienda")
            ]
            t = random.choice(themes)
            return {
                "theme": t[0],
                "sky_colors": [[10, 10, 50], [100, 50, 100]],
                "weather": t[1],
                "poetry": t[2],
                "font": t[3],
                "wind_speed": 0.2,
                "complexity": 0.2
            }
