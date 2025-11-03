FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Check ENV variable:
# If dev --> uvicorn (reload)
# Else --> gunicorn
CMD ["sh", "-c", "if [ \"$ENV\" = 'dev' ]; then uvicorn app.api:app --host 0.0.0.0 --port 8008 --reload; else gunicorn app.api:app -k uvicorn.workers.UvicornWorker -c gunicorn_conf.py; fi"]