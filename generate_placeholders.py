#!/usr/bin/env python3
"""Generate placeholder thumbnails for all cryptids without real images."""

import json
import os
import sqlite3
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent
THUMBS_DIR = Path(os.environ.get('THUMBS_DIR', str(BASE_DIR / 'static' / 'thumbs')))
FULL_DIR = Path(os.environ.get('FULL_DIR', str(BASE_DIR / 'static' / 'full')))
DB_PATH = Path(os.environ.get('DATABASE_URL', str(BASE_DIR / 'cryptid_scholar.db')))

# Create directories
THUMBS_DIR.mkdir(parents=True, exist_ok=True)
FULL_DIR.mkdir(parents=True, exist_ok=True)


def get_cryptid_type_color(cryptid_type):
    """Return color based on cryptid type."""
    colors = {
        'aquatic': (52, 152, 219),    # blue
        'terrestrial': (231, 76, 60), # red
        'flying': (155, 89, 182),     # purple
    }
    return colors.get(cryptid_type, (80, 80, 100))


def get_emoji_for_type(cryptid_type):
    """Return emoji based on cryptid type."""
    emojis = {
        'aquatic': '🌊',
        'terrestrial': '🏔️',
        'flying': '🦇',
    }
    return emojis.get(cryptid_type, '👽')


def create_placeholder_thumb(cryptid_id, cryptid_name, cryptid_type='terrestrial'):
    """Create a placeholder thumbnail with cryptid initials and type coloring."""
    thumb_path = THUMBS_DIR / f'{cryptid_id}.jpg'
    if thumb_path.exists():
        return False

    color = get_cryptid_type_color(cryptid_type)
    emoji = get_emoji_for_type(cryptid_type)

    img = Image.new('RGB', (200, 200), (color[0] // 3, color[1] // 3, color[2] // 3))
    draw = ImageDraw.Draw(img)

    # Draw border with type color
    draw.rectangle([0, 0, 199, 199], outline=color, width=3)

    # Get initials
    words = cryptid_name.split()
    if len(words) >= 2:
        initials = words[0][0] + words[-1][0]
    else:
        initials = cryptid_name[:2]

    initials = initials.upper()

    # Try to use a font, fallback to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
    except OSError:
        font = ImageFont.load_default()

    # Center text
    bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (200 - text_width) // 2
    y = (200 - text_height) // 2 - 10

    # Draw initials
    draw.text((x, y), initials, fill=(255, 255, 255), font=font)

    # Draw emoji-like text below
    try:
        emoji_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except OSError:
        emoji_font = font

    emoji_bbox = draw.textbbox((0, 0), emoji, font=emoji_font)
    emoji_width = emoji_bbox[2] - emoji_bbox[0]
    draw.text(((200 - emoji_width) // 2, 140), emoji, fill=(200, 200, 200), font=emoji_font)

    # Save thumbnail
    img.save(thumb_path, 'JPEG', quality=80)
    return True


def create_placeholder_full(cryptid_id, cryptid_name, cryptid_type='terrestrial'):
    """Create a placeholder full-size image."""
    full_path = FULL_DIR / f'{cryptid_id}.jpg'
    if full_path.exists():
        return False

    color = get_cryptid_type_color(cryptid_type)

    img = Image.new('RGB', (800, 600), (color[0] // 4, color[1] // 4, color[2] // 4))
    draw = ImageDraw.Draw(img)

    # Draw border with type color
    draw.rectangle([0, 0, 799, 599], outline=color, width=6)

    # Get initials
    words = cryptid_name.split()
    if len(words) >= 2:
        initials = words[0][0] + words[-1][0]
    else:
        initials = cryptid_name[:2]

    initials = initials.upper()

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 160)
    except OSError:
        font = ImageFont.load_default()

    # Center text
    bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (800 - text_width) // 2
    y = (600 - text_height) // 2 - 30

    draw.text((x, y), initials, fill=(255, 255, 255), font=font)

    # Draw type label
    try:
        label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except OSError:
        label_font = font

    label = f'{cryptid_type.upper()} CRYPTID'
    label_bbox = draw.textbbox((0, 0), label, font=label_font)
    label_width = label_bbox[2] - label_bbox[0]
    draw.text(((800 - label_width) // 2, 420), label, fill=(200, 200, 200), font=label_font)

    img.save(full_path, 'JPEG', quality=85)
    return True


def main():
    # Try database first, fall back to JSON
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT id, name, type FROM cryptids ORDER BY id')
        cryptids = cur.fetchall()
        conn.close()
    except sqlite3.Error:
        # Fallback to JSON seed
        seed_path = BASE_DIR / 'cryptids_seed.json'
        if seed_path.exists():
            with open(seed_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            cryptids = [(i + 1, item['name'], item.get('type', 'terrestrial')) for i, item in enumerate(data)]
        else:
            print("[!] No database or seed data found")
            return

    print(f"[*] Processing {len(cryptids)} cryptids...")

    thumbs_created = 0
    full_created = 0
    skipped = 0

    for cryptid_id, cryptid_name, cryptid_type in cryptids:
        if create_placeholder_thumb(cryptid_id, cryptid_name, cryptid_type):
            thumbs_created += 1
        else:
            skipped += 1

        if create_placeholder_full(cryptid_id, cryptid_name, cryptid_type):
            full_created += 1

    print(f"\n[+] Thumbnails created: {thumbs_created}")
    print(f"[+] Full images created: {full_created}")
    print(f"[+] Skipped (already exists): {skipped}")
    print(f"[+] Total: {len(cryptids)} cryptids")

    # Verify
    thumb_count = len(list(THUMBS_DIR.glob('*.jpg')))
    full_count = len(list(FULL_DIR.glob('*.jpg')))
    print(f"\n[✓] Thumbs directory: {thumb_count} images")
    print(f"[✓] Full directory: {full_count} images")


if __name__ == '__main__':
    main()
