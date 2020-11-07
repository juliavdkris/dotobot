FROM python:3

ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

RUN useradd -ms /bin/bash worker
USER worker
WORKDIR /home/worker
RUN mkdir storage

COPY --chown=worker:worker requirements.txt .
RUN pip install --user -r requirements.txt --no-warn-script-location


COPY --chown=worker:worker src/ app/

CMD ["python", "app/main.py"]