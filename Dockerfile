# Dockerfile
FROM python:3.11-slim

# set your workdir
WORKDIR /app

# copy just requirements, install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest of your code
COPY . .

# expose & run
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
