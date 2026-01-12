# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file (assuming build context is project root)
# Copy requirements file (assuming build context is project root)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code to /app/backend to maintain import structure
COPY backend/ /app/backend/
COPY scripts/ /app/scripts/

# Set PYTHONPATH to /app so 'backend' module can be found
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
