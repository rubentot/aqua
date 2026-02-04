# AquaRegWatch Norway - Docker Container
# Norwegian Aquaculture Regulatory Monitor

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Oslo

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/logs

# Create non-root user
RUN useradd -m -u 1000 aquaregwatch && \
    chown -R aquaregwatch:aquaregwatch /app

USER aquaregwatch

# Expose ports
EXPOSE 8501

# Health check
HEALTHCHECK --interval=5m --timeout=30s --start-period=10s --retries=3 \
    CMD python -c "from src.models import get_session; get_session()" || exit 1

# Default command (can be overridden)
CMD ["python", "main.py", "--daemon"]
