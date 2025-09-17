# Use official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# System dependencies for psycopg2 and mysql-connector
RUN apt-get update \
    && apt-get install -y gcc libpq-dev default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY main.py ./ 
COPY dashboard.html ./

# Create uploads dir
RUN mkdir -p /app/uploads

# Expose port (FastAPI default is 8000)
EXPOSE 8000

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
