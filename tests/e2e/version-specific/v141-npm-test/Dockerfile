# Dockerfile for testing claude-multiagent-pm@1.4.1 installation
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Update package manager and install git and python (required for some npm packages)
RUN apk update && apk add --no-cache git python3 py3-pip

# Create a non-root user for testing
RUN addgroup -g 1001 testuser && adduser -u 1001 -G testuser -s /bin/sh -D testuser

# Switch to test user
USER testuser

# Set up clean npm environment
RUN npm config set prefix /home/testuser/.npm-global
ENV PATH="/home/testuser/.npm-global/bin:${PATH}"

# Copy test script
COPY --chown=testuser:testuser test-v141-installation.sh /app/test-v141-installation.sh
RUN chmod +x /app/test-v141-installation.sh

# Set entrypoint to run our test script
ENTRYPOINT ["/app/test-v141-installation.sh"]