FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc libffi-dev \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p staticfiles media logs db && chmod -R 777 /app

RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py seed_data && python manage.py runserver 0.0.0.0:8000"]
