#!/usr/bin/env python3
"""Generate iOS/PWA app icons for Cryptid Scholar."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path('/root/cryptid-scholar/static')
BASE_DIR.mkdir(parents=True, exist_ok=True)


def create_icon(size, path):
    # Deep purple background
    img = Image.new('RGBA', (size, size), (10, 0, 26, 255))
    draw = ImageDraw.Draw(img)

    # Outer border/glow effect
    padding = size // 10
    border_color = (155, 89, 182, 255)  # Purple
    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=size // 5,
        fill=(20, 0, 40, 255),
        outline=border_color,
        width=max(2, size // 32)
    )

    # Draw creature emoji (👽 for cryptid)
    try:
        font_size = size // 2
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    emoji = "👽"
    bbox = draw.textbbox((0, 0), emoji, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 5

    draw.text((x, y), emoji, fill=(255, 255, 255, 255), font=font)

    # Draw "C" for Cryptid Scholar in the bottom-right corner
    try:
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size // 5)
    except OSError:
        small_font = font

    label = "C"
    label_bbox = draw.textbbox((0, 0), label, font=small_font)
    label_width = label_bbox[2] - label_bbox[0]
    draw.text(
        (size - label_width - padding // 2, size - size // 4),
        label,
        fill=(241, 196, 15, 255),  # Gold accent
        font=small_font
    )

    img.save(str(path), 'PNG')
    print(f"[+] Created {path} ({size}x{size})")


def main():
    create_icon(192, BASE_DIR / 'icon-192.png')
    create_icon(512, BASE_DIR / 'icon-512.png')
    create_icon(32, BASE_DIR / 'favicon.ico')
    print(f"\n[✓] Icons created in {BASE_DIR}")


if __name__ == '__main__':
    main()
