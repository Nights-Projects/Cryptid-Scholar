FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py rebuild_database.py download_images.py generate_placeholders.py generate_icons.py ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY cryptids_seed.json ./

EXPOSE 5000

# Data directory — can be overridden by volume mount
ENV DATABASE_URL=/data/cryptid_scholar.db \
    STATIC_DIR=/data/static \
    THUMBS_DIR=/data/static/thumbs \
    FULL_DIR=/data/static/full

VOLUME ["/data"]

# Initialize database and generate static assets at build time
RUN mkdir -p /data/static/thumbs /data/static/full \
    && python rebuild_database.py --json-input cryptids_seed.json \
    && python generate_placeholders.py \
    && python generate_icons.py \
    && cp static/placeholder.jpg /data/static/ 2>/dev/null || true

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
