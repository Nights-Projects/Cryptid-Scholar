#!/usr/bin/env python3
"""
Download images for cryptids from Wikimedia Commons and other sources.
Generates 200x200 thumbnails in static/thumbs/ and full-size in static/full/.
"""

import argparse
import json
import os
import sqlite3
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

try:
    from PIL.Image import Resampling
    LANCZOS = Resampling.LANCZOS
except ImportError:
    try:
        LANCZOS = Image.LANCZOS
    except AttributeError:
        LANCZOS = 3

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get('DATABASE_URL', str(BASE_DIR / 'cryptid_scholar.db')))
THUMBS_DIR = Path(os.environ.get('THUMBS_DIR', str(BASE_DIR / 'static' / 'thumbs')))
FULL_DIR = Path(os.environ.get('FULL_DIR', str(BASE_DIR / 'static' / 'full')))
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; CryptidScholar/1.0; +https://github.com/NicSparks/cryptid-scholar)'
}


def fetch_page(url, retries=3):
    """Fetch page content with retry logic."""
    last_error = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    # All retries exhausted
    print(f"  [!] Failed to fetch {url} after {retries} attempts: {last_error}")
    return None


def get_wikimedia_image_url(creature_name):
    """Query Wikimedia Commons API for actual image URL."""
    search_terms = [
        creature_name,
        creature_name.replace(' ', '_'),
    ]

    for term in search_terms:
        api_url = 'https://commons.wikimedia.org/w/api.php'
        params = {
            'action': 'query',
            'generator': 'search',
            'gsrsearch': f'intitle:{term} AND (cryptid OR monster OR creature OR beast)',
            'gsrlimit': 1,
            'prop': 'imageinfo',
            'iiprop': 'url',
            'format': 'json',
            'gsrnamespace': 6,
        }
        try:
            resp = requests.get(api_url, params=params, headers=HEADERS, timeout=15)
            data = resp.json()
            pages = data.get('query', {}).get('pages', {})
            for page_data in pages.values():
                if 'imageinfo' in page_data:
                    return page_data['imageinfo'][0]['url']
        except (requests.RequestException, KeyError, ValueError):
            continue

    # Fallback: direct file name approach
    filenames = [
        f'{term}.jpg',
        f'{term}.jpeg',
        f'{term}.png',
    ]
    for filename in filenames:
        api_url = 'https://commons.wikimedia.org/w/api.php'
        params = {
            'action': 'query',
            'titles': f'File:{filename}',
            'prop': 'imageinfo',
            'iiprop': 'url',
            'format': 'json'
        }
        try:
            resp = requests.get(api_url, params=params, headers=HEADERS, timeout=15)
            data = resp.json()
            pages = data.get('query', {}).get('pages', {})
            for page_data in pages.values():
                if 'imageinfo' in page_data:
                    return page_data['imageinfo'][0]['url']
        except (requests.RequestException, KeyError, ValueError):
            continue

    return None


def download_and_thumbnail(image_url, cryptid_id):
    """Download image and create thumbnail."""
    try:
        resp = requests.get(image_url, headers=HEADERS, timeout=30, allow_redirects=True)
        resp.raise_for_status()

        img = Image.open(BytesIO(resp.content))

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Save full-size
        full_path = FULL_DIR / f'{cryptid_id}.jpg'
        img.save(full_path, 'JPEG', quality=85)

        # Create thumbnail (200x200 square, centered)
        thumb = img.copy()
        thumb.thumbnail((200, 200), LANCZOS)

        thumb_square = Image.new('RGB', (200, 200), (30, 30, 40))
        offset = ((200 - thumb.width) // 2, (200 - thumb.height) // 2)
        thumb_square.paste(thumb, offset)

        thumb_path = THUMBS_DIR / f'{cryptid_id}.jpg'
        thumb_square.save(thumb_path, 'JPEG', quality=80)

        return True
    except (requests.RequestException, OSError, ValueError) as e:
        print(f'  [!] Failed: {e}')
        return False


def main():
    parser = argparse.ArgumentParser(description='Download and thumbnail cryptid images')
    parser.add_argument('--limit', type=int, default=0, help='Limit cryptids to process')
    parser.add_argument('--skip-existing', action='store_true', help='Skip cryptids that already have thumbnails')
    parser.add_argument('--force', action='store_true', help='Force re-download even if thumbnail exists')
    args = parser.parse_args()

    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    FULL_DIR.mkdir(parents=True, exist_ok=True)

    # Load cryptid data from JSON seed
    seed_path = BASE_DIR / 'cryptids_seed.json'
    if seed_path.exists():
        with open(seed_path, 'r', encoding='utf-8') as f:
            cryptid_data = json.load(f)
    else:
        # Fallback to database
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT id, name, image_url FROM cryptids WHERE image_url IS NOT NULL AND image_url != ""')
        cryptid_data = [{'id': row[0], 'name': row[1], 'image_url': row[2]} for row in cur.fetchall()]
        conn.close()

    if args.limit > 0:
        cryptid_data = cryptid_data[:args.limit]

    print(f'[*] Found {len(cryptid_data)} cryptids to process')
    print(f'[*] Thumbs dir: {THUMBS_DIR}')
    print(f'[*] Full dir: {FULL_DIR}')

    downloaded = 0
    skipped = 0
    failed = 0

    for i, cryptid in enumerate(cryptid_data, 1):
        name = cryptid.get('name', str(cryptid.get('id', 'unknown')))
        # Use name for filename since IDs might not align with DB
        cryptid_id = cryptid.get('id', i)
        existing_url = cryptid.get('image_url', '')

        thumb_path = THUMBS_DIR / f'{cryptid_id}.jpg'

        if not args.force and thumb_path.exists() and args.skip_existing:
            skipped += 1
            continue

        print(f'  [{i}/{len(cryptid_data)}] {name}')

        # Try existing URL first
        image_url = existing_url
        if not image_url:
            image_url = get_wikimedia_image_url(name)
            if not image_url:
                print(f'    [!] No image found for {name}')
                failed += 1
                continue

        if download_and_thumbnail(image_url, cryptid_id):
            downloaded += 1
            print('    [+] Downloaded')
        else:
            failed += 1

        time.sleep(0.5)

    print('\n[*] Summary:')
    print(f'    Downloaded: {downloaded}')
    print(f'    Skipped:    {skipped}')
    print(f'    Failed:     {failed}')
    print(f'    Total:      {len(cryptid_data)}')


if __name__ == '__main__':
    main()
