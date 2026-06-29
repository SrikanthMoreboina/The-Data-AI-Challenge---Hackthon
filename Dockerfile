# Use a lightweight Python base image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer output (standard CLI configuration)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies (zero dependencies, but keeps structure standard)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entrypoint script and pipeline package
COPY rank.py .
COPY recruiter_pipeline/ recruiter_pipeline/

# Set the entrypoint to run the Python ranker CLI tool
ENTRYPOINT ["python", "rank.py"]
