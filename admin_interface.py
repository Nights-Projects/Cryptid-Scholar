#!/usr/bin/env python3
"""
Admin Interface for Cryptid Scholar
Minimal authenticated web UI for managing cryptid data on the server.
Built as a Flask blueprint to be registered in the main app.
"""

import os
import sqlite3
from pathlib import Path

from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', '')  # Must be set
ADMIN_SECRET = os.environ.get('SECRET_KEY', 'default-dev-key')

DB_PATH = os.environ.get('DATABASE_URL', '/data/cryptid_scholar.db')
BASE_DIR = Path(__file__).resolve().parent

# Simple HTML template for the admin panel
ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cryptid Scholar — Admin Panel</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
  body { background: #0a001a; color: #e8e8f0; min-height: 100vh; }
  .login-card { max-width: 360px; margin: 80px auto; background: #140028; border: 1px solid #331a4d; border-radius: 16px; padding: 32px; }
  .login-card h1 { color: #f1c40f; font-size: 24px; margin-bottom: 16px; }
  .form-group { margin-bottom: 16px; }
  .form-group label { display: block; font-size: 14px; color: #8888aa; margin-bottom: 6px; }
  .form-group input { width: 100%; padding: 10px; background: #0a001a; border: 1px solid #331a4d; border-radius: 8px; color: #e8e8f0; font-size: 14px; }
  .btn { width: 100%; padding: 12px; background: #f1c40f; color: #0a001a; border: none; border-radius: 8px; font-size: 14px; font-weight: 700; cursor: pointer; }
  .btn:hover { background: #e6b800; }
  .dashboard { display: grid; gap: 16px; padding: 24px; max-width: 800px; margin: 0 auto; }
  .card { background: #140028; border: 1px solid #331a4d; border-radius: 12px; padding: 20px; }
  .card h2 { color: #f1c40f; font-size: 18px; margin-bottom: 12px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #331a4d; font-size: 13px; }
  th { color: #8888aa; }
  .stat { font-size: 2em; font-weight: 700; color: #f1c40f; }
  .logout { color: #8888aa; font-size: 12px; cursor: pointer; }
</style>
</head>
<body>
{% if not session.get('admin_authenticated') %}
<div class="login-card">
  <h1>👮 Cryptid Scholar Admin</h1>
  <form method="POST" action="/admin/login">
    <div class="form-group">
      <label>Username</label>
      <input type="text" name="username" required autofocus>
    </div>
    <div class="form-group">
      <label>Password</label>
      <input type="password" name="password" required>
    </div>
    <button class="btn" type="submit">Access Admin</button>
  </form>
</div>
{% else %}
<div class="dashboard">
  <div style="display: flex; justify-content: space-between; align-items: center;">
    <h2>📊 Dashboard</h2>
    <a href="/admin/logout" class="logout">Logout</a>
  </div>
  <div class="card">
    <h2>Database Stats</h2>
    <table>
      <tr><th>Total Cryptids</th><td class="stat">{{ stats.total or 0 }}</td></tr>
      <tr><th>Type Breakdown</th><td><span style="color:#3498db">Aquatic</span>: {{ stats.type_counts.aquatic or 0 }} | <span style="color:#e74c3c">Terrestrial</span>: {{ stats.type_counts.terrestrial or 0 }} | <span style="color:#9b59b6">Flying</span>: {{ stats.type_counts.flying or 0 }}</td></tr>
      <tr><th>Countries Covered</th><td>{{ stats.countries|length if stats.countries else 0 }}</td></tr>
    </table>
  </div>
  <div class="card">
    <h2>Maintenance</h2>
    <p style="color: #8888aa; font-size: 13px; margin-bottom: 12px;">Run data operations on the server</p>
    <form method="POST" action="/admin/actions/rebuild" style="margin-bottom: 8px;">
      <button class="btn" style="background: #3498db; color: white;" type="submit">🔄 Rebuild Database</button>
    </form>
    <form method="POST" action="/admin/actions/update">
      <button class="btn" style="background: #9b59b6; color: white;" type="submit">🔍 Update from Wikipedia</button>
    </form>
  </div>
</div>
{% endif %}
</body>
</html>
'''


def check_auth():
    """Check if the current session is authenticated."""
    return session.get('admin_authenticated')


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        # Verify credentials
        if (username == ADMIN_USERNAME and
                check_password_hash(ADMIN_PASSWORD_HASH, password)):
            session['admin_authenticated'] = True
            session.permanent = True
            return redirect(url_for('admin.dashboard'))
        return render_template_string(ADMIN_TEMPLATE, stats={}, error="Invalid credentials")

    return render_template_string(ADMIN_TEMPLATE, stats={}, error=None)


@admin_bp.route('/logout')
def logout():
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin.login'))


@admin_bp.route('/dashboard')
def dashboard():
    if not check_auth():
        return redirect(url_for('admin.login'))

    # Get stats from the database
    conn = sqlite3.connect(str(DB_PATH)) if Path(str(DB_PATH)).exists() else None
    if conn:
        conn.row_factory = sqlite3.Row
        total = conn.execute('SELECT COUNT(*) FROM cryptids').fetchone()[0]
        types = conn.execute('SELECT type, COUNT(*) as cnt FROM cryptids GROUP BY type').fetchall()
        countries = conn.execute(
            'SELECT DISTINCT country FROM cryptids WHERE country IS NOT NULL'
        ).fetchall()
        conn.close()

        # Build type_counts dict for cleaner template display
        type_counts = {}
        for row in [dict(r) for r in types]:
            type_counts[row['type']] = row['cnt']

        stats = {
            'total': total,
            'types': [dict(r) for r in types],
            'type_counts': {
                'aquatic': type_counts.get('aquatic', 0),
                'terrestrial': type_counts.get('terrestrial', 0),
                'flying': type_counts.get('flying', 0),
            },
            'countries': [dict(r) for r in countries]
        }
    else:
        stats = {'total': 0, 'types': [], 'countries': []}

    return render_template_string(ADMIN_TEMPLATE, stats=stats)


@admin_bp.route('/actions/rebuild', methods=['POST'])
def action_rebuild():
    """Rebuild database from seed data."""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 403
    import subprocess
    try:
        result = subprocess.run(
            ['python3', str(BASE_DIR / 'rebuild_database.py'), '--json-input', str(BASE_DIR / 'cryptids_seed.json')],
            capture_output=True, text=True, timeout=300, check=False
        )
        return jsonify({
            'success': True,
            'output': result.stdout,
            'stderr': result.stderr
        })
    except Exception:
        return jsonify({'success': False, 'error': 'Rebuild failed'}), 500


@admin_bp.route('/actions/update', methods=['POST'])
def action_update():
    """Run incremental crawler and apply updates."""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 403
    import subprocess
    try:
        # Run update
        result = subprocess.run(
            ['python3', str(BASE_DIR / 'crawl_new_cryptids.py'), '--apply'],
            capture_output=True, text=True, timeout=120, check=False
        )
        # Rebuild DB
        result2 = subprocess.run(
            ['python3', str(BASE_DIR / 'rebuild_database.py'), '--json-input', str(BASE_DIR / 'cryptids_seed.json')],
            capture_output=True, text=True, timeout=120, check=False
        )
        return jsonify({
            'success': True,
            'crawler_output': result.stdout,
            'rebuild_output': result2.stdout,
            'stderr': result.stderr + result2.stderr
        })
    except Exception:
        return jsonify({'success': False, 'error': 'Update failed'}), 500
