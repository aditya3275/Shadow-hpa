#!/bin/bash

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "Stopping load generation..."
    # Check if PF_PID is set and the process is running
    if [ ! -z "$PF_PID" ]; then
        echo "Killing port-forward (PID $PF_PID)..."
        kill $PF_PID 2>/dev/null
    fi
    exit 0
}

# Trap SIGINT (Ctrl+C)
trap cleanup SIGINT

echo "Setting up port-forward to php-apache..."
kubectl port-forward svc/php-apache 8080:80 > /dev/null 2>&1 &
PF_PID=$!

echo "Port-forward started (PID $PF_PID)."
echo "Waiting for connection..."
sleep 2

echo "Starting load generation loop..."
echo "---------------------------------------------------"
echo "INSTRUCTIONS:"
echo "1. Open a new terminal."
echo "2. Run: kubectl get hpa php-apache -w"
echo "3. Press Ctrl+C here to stop the load."
echo "---------------------------------------------------"

while true; do
    curl -s http://localhost:8080 > /dev/null
    # Small sleep to prevent overwhelming localhost network stack (optional)
    # sleep 0.01 
done
