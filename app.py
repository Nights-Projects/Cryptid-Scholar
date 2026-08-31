#!/usr/bin/env python3
"""
Cryptid Scholar - Mobile-first API server for learning about cryptids from around the world.
Adapted from Breed Scholar for the cryptozoology community.
Serves JSON API (port 9004) + authenticated Admin UI (port 9005)
"""

import os
import sqlite3
from pathlib import Path, PurePosixPath
from urllib.parse import unquote

from flask import Flask, jsonify, request, send_file, abort

from admin_interface import admin_bp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default-dev-key')

BASE_DIR = Path(os.environ.get('BASE_DIR', '/root/cryptid-scholar'))
DB_PATH = Path(os.environ.get('DATABASE_URL', str(BASE_DIR / 'cryptid_scholar.db')))
THUMBS_DIR = Path(os.environ.get('THUMBS_DIR', str(BASE_DIR / 'static' / 'thumbs')))
FULL_DIR = Path(os.environ.get('FULL_DIR', str(BASE_DIR / 'static' / 'full')))
THUMBS_DIR.mkdir(parents=True, exist_ok=True)
FULL_DIR.mkdir(parents=True, exist_ok=True)

# Register admin blueprint (served on /admin/*)
app.register_blueprint(admin_bp)

# Cryptid type colors
TYPE_COLORS = {
    'aquatic': '#3498db',
    'terrestrial': '#e74c3c',
    'flying': '#9b59b6',
}


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def safe_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks."""
    # Decode URL-encoded chars, then take only the basename
    decoded = unquote(filename)
    # Use PurePosixPath to handle forward slashes, then take name only
    safe = PurePosixPath(decoded).name
    # Reject if the original contained path separators after decoding
    if not safe or safe != decoded.split('/')[-1].split('\\')[-1]:
        abort(400)
    return safe


@app.route('/api/cryptids/all')
def all_cryptids():
    db = get_db()
    cursor = db.execute('''
        SELECT c.id, c.name, c.type, c.country, c.location,
               c.other_names, c.description, c.fact, c.tips, c.image_url, c.source_url,
               GROUP_CONCAT(r.code, ',') as registries
        FROM cryptids c
        LEFT JOIN cryptid_registries cr ON c.id = cr.cryptid_id
        LEFT JOIN registries r ON cr.registry_id = r.id
        GROUP BY c.id
        ORDER BY c.name ASC
    ''')
    cryptids = [dict(row) for row in cursor.fetchall()]
    db.close()
    return jsonify({'cryptids': cryptids, 'total': len(cryptids)})


@app.route('/api/cryptids')
def list_cryptids():
    db = get_db()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    search = request.args.get('search', '').strip().lower()
    cryptid_type = request.args.get('type', '').lower()
    country = request.args.get('country', '').strip().lower()

    base_where = 'WHERE 1=1'
    base_params = []

    if search:
        base_where += ' AND LOWER(c.name) LIKE ?'
        base_params.append(f'%{search}%')

    if cryptid_type:
        base_where += ' AND LOWER(c.type) = ?'
        base_params.append(cryptid_type)

    if country:
        base_where += ' AND LOWER(c.country) LIKE ?'
        base_params.append(f'%{country}%')

    query = f'''
        SELECT c.id, c.name, c.type, c.country, c.location,
               c.other_names, c.description, c.fact, c.tips, c.image_url, c.source_url,
               GROUP_CONCAT(r.code, ',') as registries
        FROM cryptids c
        LEFT JOIN cryptid_registries cr ON c.id = cr.cryptid_id
        LEFT JOIN registries r ON cr.registry_id = r.id
        {base_where}
        GROUP BY c.id
        ORDER BY c.name ASC
        LIMIT ? OFFSET ?
    '''
    offset = (page - 1) * per_page
    cursor = db.execute(query, [*base_params, per_page, offset])
    cryptids = [dict(row) for row in cursor.fetchall()]

    count_query = f'SELECT COUNT(DISTINCT c.id) FROM cryptids c {base_where}'
    total = db.execute(count_query, base_params).fetchone()[0]

    db.close()

    return jsonify({
        'cryptids': cryptids,
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page
    })


@app.route('/api/cryptids/<int:cryptid_id>')
def get_cryptid(cryptid_id):
    db = get_db()
    cursor = db.execute('''
        SELECT c.id, c.name, c.type, c.country, c.location,
               c.other_names, c.description, c.fact, c.tips, c.image_url, c.source_url,
               GROUP_CONCAT(r.code, ',') as registries
        FROM cryptids c
        LEFT JOIN cryptid_registries cr ON c.id = cr.cryptid_id
        LEFT JOIN registries r ON cr.registry_id = r.id
        WHERE c.id = ?
        GROUP BY c.id
    ''', (cryptid_id,))
    cryptid = cursor.fetchone()
    db.close()

    if cryptid:
        return jsonify(dict(cryptid))
    return jsonify({'error': 'Cryptid not found'}), 404


@app.route('/api/stats')
def get_stats():
    db = get_db()

    total = db.execute('SELECT COUNT(*) FROM cryptids').fetchone()[0]
    aquatic = db.execute('SELECT COUNT(*) FROM cryptids WHERE type = ?', ('aquatic',)).fetchone()[0]
    terrestrial = db.execute('SELECT COUNT(*) FROM cryptids WHERE type = ?', ('terrestrial',)).fetchone()[0]
    flying = db.execute('SELECT COUNT(*) FROM cryptids WHERE type = ?', ('flying',)).fetchone()[0]

    country_counts = db.execute('''
        SELECT country, COUNT(*) as cnt FROM cryptids WHERE country IS NOT NULL
        GROUP BY country ORDER BY cnt DESC LIMIT 10
    ''').fetchall()

    type_counts = db.execute('''
        SELECT type, COUNT(*) as cnt FROM cryptids GROUP BY type ORDER BY cnt DESC
    ''').fetchall()

    db.close()

    return jsonify({
        'total': total,
        'aquatic': aquatic,
        'terrestrial': terrestrial,
        'flying': flying,
        'countries': [dict(row) for row in country_counts],
        'types': [dict(row) for row in type_counts],
    })


@app.route('/api/rebuild', methods=['POST'])
def rebuild_database():
    import subprocess
    try:
        result = subprocess.run(
            ['python3', str(BASE_DIR / 'rebuild_database.py'), '--json-input', str(BASE_DIR / 'cryptids_seed.json')],
            capture_output=True,
            text=True,
            timeout=300,
            check=False
        )
        return jsonify({
            'success': True,
            'output': result.stdout,
            'errors': result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Rebuild timed out'}), 500
    except (OSError, ValueError, RuntimeError):
        return jsonify({'success': False, 'error': 'Rebuild failed'}), 500


@app.route('/api/update', methods=['POST'])
def update_data():
    """Run the incremental crawler and apply updates to the seed + database."""
    import subprocess
    try:
        # Run the crawler with --apply flag
        result = subprocess.run(
            ['python3', str(BASE_DIR / 'crawl_new_cryptids.py'), '--apply'],
            capture_output=True,
            text=True,
            timeout=120,
            check=False
        )

        # After applying, rebuild the database
        result2 = subprocess.run(
            ['python3', str(BASE_DIR / 'rebuild_database.py'), '--json-input', str(BASE_DIR / 'cryptids_seed.json')],
            capture_output=True,
            text=True,
            timeout=120,
            check=False
        )

        return jsonify({
            'success': True,
            'crawler_output': result.stdout,
            'rebuild_output': result2.stdout,
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Update timed out'}), 500
    except (OSError, ValueError, RuntimeError):
        return jsonify({'success': False, 'error': 'Update failed'}), 500


@app.route('/static/thumbs/<filename>')
def serve_thumb(filename: str):
    safe_name = safe_filename(filename)
    thumb_path = THUMBS_DIR / safe_name
    if thumb_path.exists():
        return send_file(str(thumb_path), mimetype='image/jpeg')
    placeholder = BASE_DIR / 'static' / 'placeholder.jpg'
    if placeholder.exists():
        return send_file(str(placeholder), mimetype='image/jpeg')
    return jsonify({'error': 'Not found'}), 404


@app.route('/static/full/<filename>')
def serve_full(filename: str):
    safe_name = safe_filename(filename)
    full_path = FULL_DIR / safe_name
    if full_path.exists():
        return send_file(str(full_path))
    return jsonify({'error': 'Image not cached'}), 404


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'cryptid-scholar-api'})


# Admin UI routes are handled by admin_interface.py blueprint (port 9005 via gunicorn)


if __name__ == '__main__':
    port = int(os.environ.get('API_PORT', 9004))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')