#!/usr/bin/env python3
"""Test suite for Cryptid Scholar — runs in CI to validate the build."""

import json
import sqlite3
import sys
from pathlib import Path

# Ensure we can find the project root
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_database():
    """Check that the database exists and has data."""
    db_path = Path('cryptid_scholar.db')
    assert db_path.exists(), f"Database not found at {db_path.resolve()}"

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM cryptids')
    total = cursor.fetchone()[0]
    print(f"✓ Database valid: {total} cryptids")
    assert total > 0, "Database has no cryptids"

    cursor.execute('SELECT name, type, country FROM cryptids LIMIT 3')
    for row in cursor.fetchall():
        print(f"  Sample: {row['name']} ({row['type']}) — {row['country']}")

    conn.close()


def test_seed_json():
    """Check that the seed JSON is valid."""
    seed_path = Path('cryptids_seed.json')
    assert seed_path.exists(), "Seed JSON not found"

    with open(seed_path) as f:
        cryptids = json.load(f)
    print(f"✓ Seed JSON valid: {len(cryptids)} cryptids")
    assert len(cryptids) > 0, "Seed JSON is empty"

    for c in cryptids[:3]:
        assert 'name' in c, f"Missing name in {c}"
        assert 'type' in c, f"Missing type in {c}"


def test_admin_blueprint():
    """Check that admin interface module loads."""
    from admin_interface import admin_bp
    assert admin_bp is not None, "Admin blueprint not created"
    print("✓ Admin blueprint registered")


def test_flask_app():
    """Check that Flask app imports cleanly."""
    from app import app
    assert app is not None, "Flask app not created"
    print("✓ Flask app imports successfully")

    rules = [rule.rule for rule in app.url_map.iter_rules()]
    assert '/api/cryptids' in rules, "Missing /api/cryptids route"
    assert '/api/stats' in rules, "Missing /api/stats route"
    assert '/admin/login' in rules, "Missing /admin/login route"
    print(f"✓ Routes verified: {[r for r in rules if r.startswith('/api') or r.startswith('/admin')]}")
