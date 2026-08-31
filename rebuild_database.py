#!/usr/bin/env python3
"""
Rebuild cryptid_scholar.db from a seed JSON file.
Usage: python rebuild_database.py [--json-input cryptids_seed.json] [--skip-crawl]
"""

import argparse
import json
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('DATABASE_URL', str(BASE_DIR / 'cryptid_scholar.db')))

# Cryptid registry codes — cryptids don't have official registries,
# but we categorize by geographic/source origin
REGISTRY_MAP = {
    'folklore': 1,
    'cryptozoology': 2,
    'modern': 3,
}


def init_database():
    """Create or recreate the database schema."""
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registries (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cryptids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            other_names TEXT,
            country TEXT,
            location TEXT,
            description TEXT,
            fact TEXT,
            tips TEXT,
            image_url TEXT,
            source_url TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cryptid_registries (
            cryptid_id INTEGER NOT NULL,
            registry_id INTEGER NOT NULL,
            PRIMARY KEY (cryptid_id, registry_id),
            FOREIGN KEY (cryptid_id) REFERENCES cryptids(id),
            FOREIGN KEY (registry_id) REFERENCES registries(id)
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cryptids_name ON cryptids(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cryptids_type ON cryptids(type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cryptids_country ON cryptids(country)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cryptids_location ON cryptids(location)')

    # Insert registries
    cursor.execute("INSERT OR IGNORE INTO registries (id, code, name) VALUES (1, 'folklore', 'Traditional Folklore')")
    cursor.execute("INSERT OR IGNORE INTO registries (id, code, name) VALUES (2, 'cryptozoology', 'Cryptozoology')")
    cursor.execute("INSERT OR IGNORE INTO registries (id, code, name) VALUES (3, 'modern', 'Modern Reports')")

    conn.commit()
    conn.close()
    print("[*] Database initialized")


def populate_database(cryptid_data):
    """Insert cryptid data into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Map cryptid types to registries
    type_to_reg = {
        'aquatic': 'cryptozoology',
        'terrestrial': 'cryptozoology',
        'flying': 'cryptozoology',
    }

    for cryptid in cryptid_data:
        cursor.execute('''
            INSERT OR REPLACE INTO cryptids
            (name, type, other_names, country, location, description, fact, tips, image_url, source_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            cryptid['name'],
            cryptid.get('type', 'terrestrial'),
            cryptid.get('other_names', ''),
            cryptid.get('country', ''),
            cryptid.get('location', ''),
            cryptid.get('description', ''),
            cryptid.get('fact', ''),
            cryptid.get('tips', ''),
            cryptid.get('image_url', ''),
            cryptid.get('source_url', '')
        ))

        cryptid_id = cursor.lastrowid
        reg_code = type_to_reg.get(cryptid.get('type', 'terrestrial'), 'cryptozoology')
        reg_id = REGISTRY_MAP.get(reg_code)
        if reg_id:
            cursor.execute('INSERT OR IGNORE INTO cryptid_registries (cryptid_id, registry_id) VALUES (?, ?)',
                      (cryptid_id, reg_id))

    conn.commit()

    cursor.execute('SELECT COUNT(*) FROM cryptids')
    total = cursor.fetchone()[0]
    conn.close()

    print(f"[*] Database populated: {total} cryptids")
    return total


def main():
    parser = argparse.ArgumentParser(description='Rebuild cryptid database from seed data')
    parser.add_argument('--json-input', type=str, help='Load cryptid data from JSON file')
    parser.add_argument('--skip-crawl', action='store_true', help='Skip crawling, use existing JSON')
    args = parser.parse_args()

    # Initialize database
    init_database()

    if args.json_input:
        with open(args.json_input, 'r', encoding='utf-8') as f:
            cryptid_data = json.load(f)
        print(f"[*] Loaded {len(cryptid_data)} cryptids from {args.json_input}")
    elif not args.skip_crawl:
        # Use bundled seed data
        seed_path = BASE_DIR / 'cryptids_seed.json'
        if seed_path.exists():
            with open(seed_path, 'r', encoding='utf-8') as f:
                cryptid_data = json.load(f)
            print(f"[*] Loaded {len(cryptid_data)} cryptids from seed data")
        else:
            print("[!] No data source specified. Use --json-input or create cryptids_seed.json")
            return
    else:
        print("[!] No data source specified. Use --json-input or remove --skip-crawl")
        return

    # Populate database
    total = populate_database(cryptid_data)
    print(f"[✓] Database rebuilt with {total} cryptids")
    print(f"[✓] Database location: {DB_PATH}")


if __name__ == '__main__':
    main()
