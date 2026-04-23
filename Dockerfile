# Use Python 3.9
FROM python:3.9-slim

# Create a non-root user for security (required by HF)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Install system dependencies (need to switch to root briefly)
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
USER user

# Copy requirements and install
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application
COPY --chown=user:user . .

# Hugging Face Spaces run on port 7860
EXPOSE 7860

# Start the application
CMD ["python", "api.py"]
