FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_ENGINE=sqlite \
    DJANGO_DEBUG=true \
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
