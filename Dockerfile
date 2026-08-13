FROM python:3.12-slim

WORKDIR /app

# Install FFmpeg and required system libraries
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libass9 \
    fonts-dejavu \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for running the application
# Using UID 1000 for better compatibility with volume mounts
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g 1000 -s /sbin/nologin -c "Application user" appuser

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app

# Create output directory with proper permissions
# The directory will be created by OutputManager on startup
# but we ensure it exists with correct ownership
RUN mkdir -p /output && \
    chown 1000:1000 /output && \
    chmod 755 /output

# Ensure app directory has correct permissions
RUN chown -R 1000:1000 /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
