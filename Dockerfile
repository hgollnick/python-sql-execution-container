# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables for UTF-8 and unbuffered output
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any necessary dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user and switch to it (for security)
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Run the Python script
CMD ["python", "app.py"]
