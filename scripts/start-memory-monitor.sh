#!/bin/bash

# Claude PM Framework - Memory Monitor Service
export NODE_OPTIONS='--max-old-space-size=8192 --gc-interval=100 --expose-gc'

cd "/Users/masa/Projects/claude-multiagent-pm"

# Start memory monitor in background
echo "🧠 Starting Claude PM Memory Monitor..."
node scripts/memory-monitor.js &
MONITOR_PID=$!

echo "📊 Memory Monitor started with PID: $MONITOR_PID"
echo $MONITOR_PID > logs/memory-monitor.pid

# Start memory guard
echo "🛡️ Starting Memory Guard System..."
node scripts/memory-guard.js monitor &
GUARD_PID=$!

echo "🛡️ Memory Guard started with PID: $GUARD_PID"
echo $GUARD_PID > logs/memory-guard.pid

echo "✅ Memory optimization system fully active"
echo "📝 Logs available in: logs/"
echo "📊 Dashboard: logs/memory-dashboard.json"
echo "🛡️ Guard logs: logs/memory-guard.log"

# Keep script running
wait
