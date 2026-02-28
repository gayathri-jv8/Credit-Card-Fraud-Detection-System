# 1. Use an official, slim Python base image
FROM python:3.9-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Install system dependencies (for building some Python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*


RUN apt-get update && apt-get install -y ffmpeg

# 4. Copy the requirements file first (Optimization: Docker Cache)
COPY requirements.txt .

# 5. Install Python dependencies
RUN pip install -r requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# 6. Copy the model and code into the container
COPY . .

# 7. Expose the port Flask Project runs on
EXPOSE 5000

# 8. Command to run the application
CMD ["python", "app.py"]


# docker build -t app:v1 .
# docker run -p 5000:5000 app:v1