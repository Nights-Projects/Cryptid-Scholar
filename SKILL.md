# Cryptid Scholar

Mobile-first PWA for learning about cryptids from around the world.

This skill helps bootstrap a new Cryptid Scholar project mirroring the Breed Scholar architecture.

## Project Structure

```
cryptid-scholar/
├── app.py                    # Flask app with API endpoints
├── rebuild_database.py       # Rebuild SQLite from seed JSON
├── download_images.py        # Download cryptid images from Wikimedia Commons
├── generate_placeholders.py  # Generate placeholder thumbnails for missing images
├── generate_icons.py         # Generate PWA app icons
├── cryptids_seed.json        # Seed data: 48 cryptids from Wikipedia
├── requirements.txt          # Python dependencies
├── Dockerfile                # Multi-stage Docker build
├── docker-compose.yml        # Local dev compose
├── templates/
│   └── index.html            # Main PWA UI
├── static/
│   ├── app.js                # Frontend JavaScript
│   ├── icon-192.png          # PWA icon
│   ├── icon-512.png          # PWA icon
│   └── favicon.ico           # Favicon
├── data/                     # Docker volume mount
│   ├── cryptid_scholar.db    # SQLite database
│   └── static/               # Cached images
└── .github/
    └── workflows/
        └── docker-build.yml  # CI/CD pipeline
```

## Cryptid Data Model

Each cryptid entry in the seed JSON contains:
- `name` — Primary name (e.g., "Loch Ness Monster")
- `type` — One of: `aquatic`, `terrestrial`, `flying`
- `other_names` — Aliases (e.g., "Nessie, Loch Ness Monster")
- `country` — Country of origin
- `location` — Specific location (region, lake, forest)
- `description` — Brief physical description
- `fact` — Detailed fact paragraph
- `tips` — Identification tips for the quiz
- `image_url` — Wikimedia Commons image URL (may be empty)
- `source_url` — Source Wikipedia article URL