import psutil
import datetime
import random

class Sensors:
    def __init__(self):
        pass

    def get_system_stats(self):
        """
        Returns a dictionary containing current system statistics.
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram_percent = psutil.virtual_memory().percent
        return {
            "cpu": cpu_percent,
            "ram": ram_percent
        }

    def get_time_context(self):
        """
        Returns time-related context (time of day, approximate 'mood' of the hour).
        """
        now = datetime.datetime.now()
        hour = now.hour
        
        if 5 <= hour < 12:
            period = "morning"
        elif 12 <= hour < 17:
            period = "afternoon"
        elif 17 <= hour < 21:
            period = "evening"
        else:
            period = "night"
            
        return {
            "timestamp": now.isoformat(),
            "hour": hour,
            "period": period
        }

    def get_environment_snapshot(self):
        """
        Aggregates all sensor data into a single snapshot.
        """
        stats = self.get_system_stats()
        time_ctx = self.get_time_context()
        
        # In a real app, we might fetch weather here.
        # For now, we'll add a random 'noise' factor to simulate organic variability
        noise = random.random()
        
        return {
            **stats,
            **time_ctx,
            "noise": noise
        }
