FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/sparoma-sensor-exporter.py .

# Create non-root user
RUN groupadd -r sparoma && useradd -r -g sparoma sparoma
RUN chown -R sparoma:sparoma /app
USER sparoma

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000')" || exit 1

# Set default environment variables
ENV PORT=8000
ENV CONFIG=/app/devices.json
ENV DEBUG=false

# Run the application
CMD ["python", "sparoma-sensor-exporter.py"]