FROM python:3.9-slim

# Install Docker CLI (needed for image operations)
RUN apt-get update && \
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY docker_hub_migrate.py .

# Make the script executable
RUN chmod +x docker_hub_migrate.py

# Create entrypoint script to handle Docker socket mounting instructions
RUN echo '#!/bin/sh\necho "NOTE: To use this container, you must mount the Docker socket:"\necho "docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock [image_name] [args]"\necho ""\nexec python /app/docker_hub_migrate.py "$@"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]