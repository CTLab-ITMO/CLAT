# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Add current directory to PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Copy the start_app.sh script
COPY start_app.sh /usr/local/bin/start_app.sh

# Make the script executable
RUN chmod +x /usr/local/bin/start_app.sh

# Set the entrypoint to the script
ENTRYPOINT ["/usr/local/bin/start_app.sh"]

# Start the application
#CMD ["python", "image_assessment_service/app.py", "--config", "image_assessment_service/resources/config.yml"]