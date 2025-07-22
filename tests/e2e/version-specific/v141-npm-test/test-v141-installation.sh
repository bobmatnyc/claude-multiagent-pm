#!/bin/sh

echo "=== Testing claude-multiagent-pm@1.4.1 npm installation ==="
echo "Date: $(date)"
echo "Node version: $(node --version)"
echo "NPM version: $(npm --version)"
echo ""

echo "=== Step 1: Installing @bobmatnyc/claude-multiagent-pm@1.4.1 ==="
npm install -g @bobmatnyc/claude-multiagent-pm@1.4.1

if [ $? -ne 0 ]; then
    echo "❌ Installation failed!"
    exit 1
fi

echo ""
echo "=== Step 2: Verifying installation ==="
npm list -g @bobmatnyc/claude-multiagent-pm

echo ""
echo "=== Step 3: Testing claude-pm command ==="
claude-pm --version

if [ $? -ne 0 ]; then
    echo "❌ claude-pm command not found or failed!"
    exit 1
fi

echo ""
echo "=== Step 4: Testing claude-pm help ==="
claude-pm --help

echo ""
echo "=== Step 5: Testing claude-pm init ==="
cd /tmp
mkdir test-project
cd test-project
claude-pm init

if [ $? -ne 0 ]; then
    echo "❌ claude-pm init failed!"
    exit 1
fi

echo ""
echo "=== Step 6: Checking created files ==="
ls -la

echo ""
echo "✅ All tests passed! claude-multiagent-pm@1.4.1 installed and working correctly!"