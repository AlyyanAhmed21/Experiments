#!/bin/bash

# Configuration
IDLE_THRESHOLD=900000 # 15 minutes in milliseconds
CHECK_INTERVAL=10
SCREENSAVER_CMD="python3 $(pwd)/AgenticScreensaver/main.py"

echo "Starting Agentic Screensaver Monitor..."
echo "Idle Threshold: $((IDLE_THRESHOLD / 1000)) seconds"

while true; do
    # Get idle time in milliseconds
    # Requires xprintidle: sudo apt install xprintidle
    if command -v xprintidle &> /dev/null; then
        IDLE_TIME=$(xprintidle)
    else
        # Fallback for GNOME (returns milliseconds)
        # Output format is usually "(uint32 12345,)" or similar. We extract digits only.
        IDLE_TIME=$(gdbus call --session --dest org.gnome.Mutter.IdleMonitor --object-path /org/gnome/Mutter/IdleMonitor/Core --method org.gnome.Mutter.IdleMonitor.GetIdletime | tr -dc '0-9')
    fi

    if [ -z "$IDLE_TIME" ]; then
        echo "Error: Could not detect idle time. Please install xprintidle."
        sleep 60
        continue
    fi

    if [ "$IDLE_TIME" -gt "$IDLE_THRESHOLD" ]; then
        echo "System idle detected. Launching screensaver..."
        
        # Export API Key if needed (ensure it's set in your environment or here)
        # export GEMINI_API_KEY="your_key_here"
        
        $SCREENSAVER_CMD
        
        # Wait for screensaver to exit (it exits on user input)
        echo "Screensaver exited. Resuming monitor."
        
        # Sleep a bit to avoid immediate re-trigger
        sleep 5
    fi

    sleep $CHECK_INTERVAL
done
