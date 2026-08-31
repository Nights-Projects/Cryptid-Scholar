#!/usr/bin/env python3
"""Test suite for Cryptid Scholar — runs in CI to validate the build."""

import os
import sys
import json
import sqlite3
from pathlib import Path


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
    return True


def test_seed_json():
    """Check that the seed JSON is valid."""
    seed_path = Path('cryptids_seed.json')
    assert seed_path.exists(), "Seed JSON not found"

    with open(seed_path) as f:
        cryptids = json.load(f)
    print(f"✓ Seed JSON valid: {len(cryptids)} cryptids")
    assert len(cryptids) > 0, "Seed JSON is empty"

    # Check required fields
    for c in cryptids[:3]:
        assert 'name' in c, f"Missing name in {c}"
        assert 'type' in c, f"Missing type in {c}"
    return True


def test_admin_blueprint():
    """Check that admin interface module loads."""
    from admin_interface import admin_bp
    assert admin_bp is not None, "Admin blueprint not created"
    print("✓ Admin blueprint registered")
    return True


def test_flask_app():
    """Check that Flask app imports cleanly."""
    from app import app
    assert app is not None, "Flask app not created"
    print("✓ Flask app imports successfully")

    # Verify API routes exist
    rules = [rule.rule for rule in app.url_map.iter_rules()]
    assert '/api/cryptids' in rules, "Missing /api/cryptids route"
    assert '/api/stats' in rules, "Missing /api/stats route"
    assert '/admin/login' in rules, "Missing /admin/login route"
    print(f"✓ Routes verified: {[r for r in rules if r.startswith('/api') or r.startswith('/admin')]}")
    return True


if __name__ == '__main__':
    tests = [
        test_database,
        test_seed_json,
        test_admin_blueprint,
        test_flask_app,
    ]

    failed = []
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}", file=sys.stderr)
            failed.append(test.__name__)

    if failed:
        print(f"\n❌ {len(failed)} test(s) failed: {failed}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"\n✅ All {len(tests)} tests passed")
