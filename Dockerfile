# Use a Python slim base image with Debian
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Camoufox/Playwright (Firefox)
RUN apt-get update && apt-get install -y \
    libgtk-3-0 \
    libx11-xcb1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Camoufox with geoip dataset
RUN pip install -U camoufox[geoip]

# Download Camoufox's browser (Firefox)
RUN python -m camoufox fetch

# Copy application code
COPY . .

# Expose port 5000 for Flask
EXPOSE 5000

# Run the Flask app
CMD ["python", "run.py"]