FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["python", "api/main.py"]
