#!/bin/bash

# Start mem0AI service with proper environment loading
# This script ensures the service loads environment variables correctly

echo "Starting mem0AI service with environment variables..."

# Change to the project directory
cd /Users/masa/Projects/claude-multiagent-pm

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: .env file not found"
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Error: OPENAI_API_KEY not set in environment"
    exit 1
fi

echo "OPENAI_API_KEY is configured (${#OPENAI_API_KEY} characters)"

# Kill any existing mem0 service
pkill -f mem0_service.py 2>/dev/null || true

# Start the service
echo "Starting mem0_service.py..."
python mem0_service.py
