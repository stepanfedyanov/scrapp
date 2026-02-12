FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN useradd -m appuser
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

USER appuser

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "-b", "0.0.0.0:8000", "--workers", "3", "--timeout", "60"]
