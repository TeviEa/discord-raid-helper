FROM python:3.12-slim

# Install build dependencies for PyNaCl (cffi needs gcc + libffi + libc headers + make)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libffi-dev libc6-dev make && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files
COPY . .

# Ensure data directory exists
RUN mkdir -p /app/data

# App listens on 3333 by default
EXPOSE 3333

# Run the bot
CMD ["python", "-m", "bot.server"]
