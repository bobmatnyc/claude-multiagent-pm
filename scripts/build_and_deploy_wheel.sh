#!/bin/bash
# Build and deploy Python wheel for claude-multiagent-pm

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[BUILD]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Must be run from project root directory"
    exit 1
fi

print_status "Starting claude-multiagent-pm wheel build process..."

# Step 1: Clean previous builds
print_status "Cleaning previous build artifacts..."
rm -rf build dist *.egg-info claude_multiagent_pm.egg-info

# Step 2: Ensure framework data is in place
if [ ! -d "claude_pm/data/framework" ]; then
    print_status "Copying framework directory to package data..."
    mkdir -p claude_pm/data
    cp -r framework claude_pm/data/
fi

# Step 3: Update version if needed
CURRENT_VERSION=$(grep "^version = " pyproject.toml | cut -d'"' -f2)
print_status "Building version: $CURRENT_VERSION"

# Step 4: Build the wheel
print_status "Building wheel..."
python -m build --wheel

# Step 5: Verify the wheel
print_status "Verifying wheel contents..."
if python scripts/verify_wheel.py; then
    print_status "Wheel verification passed!"
else
    print_error "Wheel verification failed!"
    exit 1
fi

# Step 6: Display build results
WHEEL_FILE=$(ls dist/*.whl 2>/dev/null | head -1)
if [ -z "$WHEEL_FILE" ]; then
    print_error "No wheel file found in dist/"
    exit 1
fi

WHEEL_SIZE=$(du -h "$WHEEL_FILE" | cut -f1)
print_status "Build complete!"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Wheel: $WHEEL_FILE"
echo "  Size:  $WHEEL_SIZE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "To install locally:"
echo "  pip install $WHEEL_FILE"
echo
echo "To upload to PyPI:"
echo "  python -m twine upload $WHEEL_FILE"
echo
echo "To test in a clean environment:"
echo "  python scripts/test_wheel_installation.py $WHEEL_FILE"