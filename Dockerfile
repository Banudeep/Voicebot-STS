FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Bind to all interfaces for Docker
ENV HOST=0.0.0.0
# Single port for both HTTP and WebSocket (Azure Container Apps compatibility)
ENV PORT=8080

# Install system dependencies (if needed for websockets)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create recordings directory (will be used if ENABLE_RECORDINGS=true)
RUN mkdir -p recordings

# Expose port
# 8080 - HTTP server (web UI) and WebSocket server (audio streaming)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080')" || exit 1

# Run the application
CMD ["python", "sts_agent.py"]

