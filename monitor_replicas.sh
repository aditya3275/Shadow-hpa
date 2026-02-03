#!/bin/bash

OUTPUT_FILE=${1:-actual_replicas.csv}

echo "Monitoring replicas for php-apache..."
echo "Output file: $OUTPUT_FILE"

# Initialize file with header if it doesn't exist
if [ ! -f "$OUTPUT_FILE" ]; then
    echo "timestamp,replicas" > "$OUTPUT_FILE"
fi

cleanup() {
    echo ""
    echo "Stopping monitor..."
    exit 0
}

trap cleanup SIGINT

while true; do
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Check if deployment exists to avoid error spam
    if kubectl get deployment php-apache > /dev/null 2>&1; then
        REPLICAS=$(kubectl get deployment php-apache -o jsonpath='{.spec.replicas}')
        echo "$TIMESTAMP,$REPLICAS" >> "$OUTPUT_FILE"
        echo "Recorded: $TIMESTAMP -> $REPLICAS"
    else
        echo "Deployment php-apache not found."
    fi
    
    sleep 15
done
