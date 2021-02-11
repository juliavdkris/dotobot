FROM python:3

ENV PYTHONUNBUFFERED=1
RUN pip install --upgrade pip

WORKDIR /root
RUN mkdir storage

COPY Procfile .

COPY requirements.txt .
RUN pip install -r requirements.txt --no-warn-script-location

COPY src/ app/

# Copy initial config files
COPY storage-template/ ./storage


CMD ["python", "app/main.py"]
