FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create static directory
RUN mkdir -p static

# Expose port (Railway provides PORT env var, default to 8000)
EXPOSE 8000

# Run the application with shell form to allow env var expansion
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
