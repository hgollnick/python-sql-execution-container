# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any necessary dependencies
RUN pip install --no-cache-dir pymssql

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the Python script
CMD ["python", "migrate_uuid4_uuid7.py"]
