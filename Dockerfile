FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py rebuild_database.py download_images.py generate_placeholders.py generate_icons.py ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY cryptids_seed.json ./

EXPOSE 5000

ENV DATABASE_URL=/data/cryptid_scholar.db
ENV STATIC_DIR=/data/static
ENV THUMBS_DIR=/data/static/thumbs
ENV FULL_DIR=/data/static/full

VOLUME ["/data"]

# Initialize database on first run if it doesn't exist
RUN python rebuild_database.py --json-input cryptids_seed.json

# Generate static assets
RUN python generate_placeholders.py && python generate_icons.py

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
