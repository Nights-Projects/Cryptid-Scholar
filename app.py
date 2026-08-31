#!/usr/bin/env python3
"""
Cryptid Scholar - Mobile-first PWA for learning about cryptids from around the world.
Adapted from Breed Scholar for the cryptozoology community.
"""

import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)

BASE_DIR = Path(os.environ.get('BASE_DIR', '/root/cryptid-scholar'))
DB_PATH = Path(os.environ.get('DATABASE_URL', str(BASE_DIR / 'cryptid_scholar.db')))
THUMBS_DIR = Path(os.environ.get('THUMBS_DIR', str(BASE_DIR / 'static' / 'thumbs')))
FULL_DIR = Path(os.environ.get('FULL_DIR', str(BASE_DIR / 'static' / 'full')))
THUMBS_DIR.mkdir(parents=True, exist_ok=True)
FULL_DIR.mkdir(parents=True, exist_ok=True)

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


@app.route('/')
def index():
    return render_template('index.html')


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
    cursor = db.execute(query, base_params + [per_page, offset])
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

    # Count by country
    country_counts = db.execute('''
        SELECT country, COUNT(*) as cnt FROM cryptids WHERE country IS NOT NULL
        GROUP BY country ORDER BY cnt DESC LIMIT 10
    ''').fetchall()

    # Count by type
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
            'stdout': result.stdout,
            'stderr': result.stderr
        })
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Rebuild timed out'}), 500
    except (OSError, ValueError, RuntimeError) as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/static/thumbs/<filename>')
def serve_thumb(filename):
    thumb_path = THUMBS_DIR / filename
    if thumb_path.exists():
        return send_file(str(thumb_path), mimetype='image/jpeg')
    placeholder = BASE_DIR / 'static' / 'placeholder.jpg'
    if placeholder.exists():
        return send_file(str(placeholder), mimetype='image/jpeg')
    return jsonify({'error': 'Not found'}), 404


@app.route('/static/full/<filename>')
def serve_full(filename):
    full_path = FULL_DIR / filename
    if full_path.exists():
        return send_file(str(full_path))
    return jsonify({'error': 'Image not cached'}), 404


@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Cryptid Scholar",
        "short_name": "CryptidScholar",
        "description": "Learn about cryptids from around the world — images, flashcards, and quizzes",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0a001a",
        "theme_color": "#6a0dad",
        "orientation": "portrait",
        "icons": [
            {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ]
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
