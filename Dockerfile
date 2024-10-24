# Use an official Python runtime as the base image
# FROM python:3.10-slim
FROM python:3.10-bullseye

# Set the working directory
WORKDIR /usr/src/app

# Install system dependencies required for Kafka and other dependencies
RUN apt-get update && apt-get install -y wget gnupg \
    && wget -qO - https://ftp-master.debian.org/keys/archive-key-10.asc | apt-key add - \
    && wget -qO - https://ftp-master.debian.org/keys/archive-key-11.asc | apt-key add - \
    && apt-get update && apt-get install -y \
    gcc \
    librdkafka-dev \
    libssl-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the necessary files into the Docker image
COPY . .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt --verbose

# Expose port 8000 for the HTTP server
EXPOSE 8000

# Command to run the server when the container starts
CMD ["python", "agent_inference.py"]
