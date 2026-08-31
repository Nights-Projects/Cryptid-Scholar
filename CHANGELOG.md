# Cryptid Scholar Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CI pipeline with security scan, lint, tests, and Docker build
- GitHub Actions workflow for multi-arch Docker image builds
- Branch protection on `main` with PR requirements and status checks

## [1.0.0] - 2026-08-30

### Added
- Initial release of Cryptid Scholar
- SQLite database with 48 world cryptids across 3 types (Aquatic, Terrestrial, Flying)
- Flask web app with mobile-first dark theme (purple accents)
- Browse, search, and filter by type feature
- Flashcard mode with 3D flip animation
- Quiz mode with multiple-choice questions
- Stats page with type breakdown and learning progress
- Wikimedia Commons image integration
- Placeholder thumbnail generation for cryptids without images
- PWA support with iOS meta tags and manifest.json
- Dockerfile and docker-compose.yml with external data mounts
