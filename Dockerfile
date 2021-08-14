FROM python:3

ENV PYTHONUNBUFFERED=1
RUN pip install --upgrade pip

COPY Procfile .
WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

# Copy initial config files
COPY storage-template/ ./storage


CMD ["python", "src/main.py"]
