import os

# API Configuration
# Try to get from environment variable, otherwise leave empty/placeholder
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyBhZBu4FuIm6S-dNmodYGm_BOHqSHCNYwk")

# Visual Configuration
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FULLSCREEN = True
FPS = 60

# Agent Configuration
DECISION_INTERVAL = 10  # Seconds between agent "thoughts"
MEMORY_DB_PATH = "memory.db"
