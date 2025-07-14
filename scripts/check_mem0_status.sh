#!/bin/bash

# Quick status check for mem0AI service
echo "=== Mem0AI Service Status Check ==="
echo "Date: $(date)"
echo

# Check if service is running
PID=$(pgrep -f mem0_service.py)
if [ -n "$PID" ]; then
    echo "✅ Service is running (PID: $PID)"
else
    echo "❌ Service is not running"
fi

# Check health endpoint
echo "🔍 Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:8002/health 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Health endpoint responding: $HEALTH_RESPONSE"
else
    echo "❌ Health endpoint not responding"
fi

# Check memory count
echo "🧠 Testing memory operations..."
MEMORY_COUNT=$(curl -s "http://localhost:8002/memories?user_id=test_user&limit=10" 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data.get('memories', {}).get('results', [])))" 2>/dev/null)
if [ -n "$MEMORY_COUNT" ]; then
    echo "✅ Memory operations working: $MEMORY_COUNT memories found"
else
    echo "❌ Memory operations not working"
fi

echo
echo "=== Service Configuration ==="
echo "Port: 8002"
echo "Host: localhost"
echo "API Docs: http://localhost:8002/docs"
echo "Log file: $(pwd)/mem0_service.log"