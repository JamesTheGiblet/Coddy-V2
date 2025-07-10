# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to prevent generating .pyc files and to run in unbuffered mode
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the project definition file first to leverage Docker layer caching
COPY pyproject.toml .

# Install the project and its dependencies
RUN pip install --no-cache-dir .

# Copy the rest of the application source code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application when the container starts
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]