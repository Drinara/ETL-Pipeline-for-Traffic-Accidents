FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    gcc \
    libpq-dev \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy app files and requirements
COPY requirements.txt .
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy and configure cron job
COPY crontab.txt /etc/cron.d/etl-cron

# Fix Windows line endings in .env file
RUN sed -i 's/\r$//' /app/.env

RUN chmod 0644 /etc/cron.d/etl-cron

# Create log file
RUN touch /var/log/cron.log

# Start cron service and keep container running
ENTRYPOINT ["sh", "-c"]
CMD ["cron && tail -f /var/log/cron.log"]


