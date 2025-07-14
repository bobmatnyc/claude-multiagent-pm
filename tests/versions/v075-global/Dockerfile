# Dockerfile for testing claude-multiagent-pm@0.7.5 installation
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Update package manager and install git (required for some npm packages)
RUN apk update && apk add --no-cache git python3 py3-pip

# Create a non-root user for testing
RUN addgroup -g 1001 testuser && adduser -u 1001 -G testuser -s /bin/sh -D testuser

# Switch to test user
USER testuser

# Set up clean npm environment
RUN npm config set prefix /home/testuser/.npm-global
ENV PATH="/home/testuser/.npm-global/bin:${PATH}"

# Copy test script
COPY --chown=testuser:testuser test-v075-installation.sh /app/test-v075-installation.sh
RUN chmod +x /app/test-v075-installation.sh

# Set entrypoint to run our test script
ENTRYPOINT ["/app/test-v075-installation.sh"]