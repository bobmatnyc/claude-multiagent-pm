#!/bin/bash
# Claude PM Framework - Memory Environment Setup

export NODE_OPTIONS="--max-old-space-size=4096 --expose-gc --gc-interval=100"
echo "🧠 Node.js memory optimization flags set:"
echo "   --max-old-space-size=4096 (4GB heap limit)"
echo "   --expose-gc (manual garbage collection)"
echo "   --gc-interval=100 (frequent GC)"
