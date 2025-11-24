import time
import threading
from .sensors import Sensors
from .memory import Memory
from .brain import Brain
from visualizer.engine import VisualEngine
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FULLSCREEN, DECISION_INTERVAL

class Agent:
    def __init__(self):
        print("Initializing Agent...")
        self.sensors = Sensors()
        self.memory = Memory()
        self.brain = Brain()
        self.visualizer = VisualEngine(SCREEN_WIDTH, SCREEN_HEIGHT, FULLSCREEN)
        
        self.last_decision_time = 0
        self.session_id = None
        self.current_theme = "Startup"

    def run(self):
        print("Agent starting...")
        self.session_id = self.memory.log_session_start()
        
        # Initial decision
        self._make_decision()

        try:
            while self.visualizer.running:
                # 1. Observe & Think (Periodically)
                if time.time() - self.last_decision_time > DECISION_INTERVAL:
                    self._make_decision()

                # 2. Render
                self.visualizer.render()
                
        except KeyboardInterrupt:
            pass
        finally:
            self._shutdown()

    def _make_decision(self):
        print("Agent thinking...")
        # Observe
        env_data = self.sensors.get_environment_snapshot()
        history = self.memory.get_recent_history()
        
        # Think
        decision = self.brain.decide(env_data, history)
        print(f"Decision made: {decision.get('theme')}")
        
        # Act
        self.visualizer.update_state(decision)
        self.last_decision_time = time.time()
        self.current_theme = decision.get("theme", "Unknown")
        
        # Remember
        self.memory.save_creative_output("decision", decision, env_data)

    def _shutdown(self):
        print("Agent shutting down...")
        avg_cpu = 0 # Placeholder for session stats
        self.memory.update_session_end(self.session_id, self.current_theme, avg_cpu)
        self.visualizer.quit()
