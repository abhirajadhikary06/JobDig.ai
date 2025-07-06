# Use official Python slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file first to leverage Docker cache
COPY requirements.txt .

# Install system dependencies and Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads/profiles

# Set environment variables
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5001

# Run the application with Flask's built-in server
CMD ["python", "main.py"]