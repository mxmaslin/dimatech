FROM python:3.12-slim

WORKDIR /app

# All dependencies provide binary wheels for python:3.12-slim, no build tools needed.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install --no-cache-dir -e .

RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --gid 1001 appuser \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD alembic upgrade head && sanic src.main:create_app --factory --host=0.0.0.0 --port=8000
