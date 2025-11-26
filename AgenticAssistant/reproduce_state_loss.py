
import os
import sys
from database.db_manager import DatabaseManager
from agents.creative_agent import CreativeAgent

# Setup
db_path = "test_data/test.db"
if os.path.exists(db_path):
    os.remove(db_path)
    
db = DatabaseManager(db_path)
user = db.create_user("test_user")
user_id = user.user_id

# 1. Start a game
agent = CreativeAgent(db)
print(f"Initial state: {agent.active_game}")

response = agent.process(user_id, "let's play a word game")
print(f"Response 1: {response[:50]}...")
print(f"State after request: {agent.active_game}")

# 2. Simulate app restart (new agent instance)
print("\n--- Simulating Restart ---")
new_agent = CreativeAgent(db)
print(f"New Agent State: {new_agent.active_game}")

# 3. Check if it can recover state from DB
# Currently it doesn't have logic for this, so we expect None
if new_agent.active_game is None:
    print("FAIL: State lost after restart")
else:
    print(f"SUCCESS: State recovered: {new_agent.active_game}")

# 4. Verify DB has the metadata
history = db.get_conversation_history(user_id, limit=1)
if history:
    last_conv = history[0]
    print(f"\nLast DB Entry Metadata: {last_conv.metadata}")
