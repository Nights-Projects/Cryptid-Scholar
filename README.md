# Cryptid Scholar

Mobile-first PWA for learning about cryptids from around the world — 48+ creatures, real images, flashcards, quizzes, and dark theme.

A spiritual cousin to [Breed Scholar](https://github.com/NicSparks/breed-scholar), but built for the cryptozoology community instead of dog breeds.

## Quick Start

```bash
docker compose up --build
```

Web UI: `http://localhost:8000`

## Tech Stack

- **Flask** web backend with SQLite database
- **Vanilla JS** mobile-first PWA frontend
- **Wikimedia Commons** API for cryptid images
- **Docker** containerization with Docker Compose
- **GitHub Actions** CI/CD with multi-arch builds

## Features

- 📱 **Mobile-first PWA** — works as a web app on iOS, Android, and desktop
- 🌒 **Dark theme** — purple-accented dark mode designed for nighttime cryptid research
- 🔍 **Browse & search** — filter by type (Aquatic, Terrestrial, Flying), search by name, location, or country
- 💳 **Flashcards** — 3D flip cards with cryptid images and facts
- 🧠 **Quiz mode** — test your cryptid knowledge with multiple-choice questions
- 📊 **Stats** — track your learning progress with local storage

## Cryptid Types

| Type | Description | Color |
|------|-------------|-------|
| 🌊 **Aquatic** | Lake monsters, sea serpents, water cryptids | Blue |
| 🏔️ **Terrestrial** | Forest beasts, hominids, land-based creatures | Red |
| 🦇 **Flying** | Winged cryptids, aerial creatures | Purple |

## Database

The SQLite database (`cryptid_scholar.db`) contains 48 cryptids sourced from Wikipedia's "List of cryptids" and related articles. Each cryptid has:

- Name, type, description, fact, identification tips
- Location and country of origin
- Other aliases/names
- Wikimedia Commons image URL

## Rebuilding the Database

```bash
# Rebuild from seed data
docker compose exec web python rebuild_database.py --json-input cryptids_seed.json

# Download real images from Wikimedia Commons
docker compose exec web python download_images.py

# Generate placeholder thumbnails
docker compose exec web python generate_placeholders.py
```

## Volumes & Backup

- `./data` → `/data`
- Database: `/data/cryptid_scholar.db`
- Static assets: `/data/static/`

## CI/CD

- Docker image is built automatically in GitHub Actions on merge to `main`
- Image is pushed to GitHub Packages: `ghcr.io/NicSparks/cryptid-scholar`
- Multi-arch builds: `linux/amd64, linux/arm64`

## License

MIT

## Credits

- Based on the architecture of [Breed Scholar](https://github.com/NicSparks/breed-scholar)
- Cryptid data sourced from [Wikipedia: List of cryptids](https://en.wikipedia.org/wiki/List_of_cryptids)
- Images sourced from Wikimedia Commons
