#!/bin/bash
# Docker-based Test Deployment for EP-0043 Refactoring
# Completely isolated from host system

set -e

echo "🐳 Claude PM Refactoring - Docker Test Deployment"
echo "================================================="
echo ""
echo "This test runs in a Docker container - completely isolated from your system."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Create Dockerfile for test environment
cat > Dockerfile.test << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the project
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir pytest pytest-cov pytest-asyncio

# Run validation script
CMD ["python", "scripts/validate_refactoring.py"]
EOF

# Build Docker image
echo "Building Docker test image..."
docker build -f Dockerfile.test -t claude-pm-refactor-test .

# Run tests in container
echo ""
echo "Running tests in Docker container..."
docker run --rm claude-pm-refactor-test

# Cleanup
rm -f Dockerfile.test

echo ""
echo "✅ Docker test deployment complete!"
echo ""
echo "The test ran in complete isolation from your system."