FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN mkdir -p /app/data

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    fonts-dejavu \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run the bot
CMD ["python", "src/bot.py"]
