# Cryptid Scholar — Android Client

A lightweight Kotlin Android app for exploring cryptids from around the world.

## Features

- 📚 Browse all 63 cryptids with local details
- 📊 View statistics (total, by type: Aquatic, Terrestrial, Flying)
- 🔍 Search and filter by type/country
- 🔄 Pull-to-refresh data from the API

## API

Connects to `https://cryptids.nicscreations.com/api/`

## Building

```bash
cd cryptid-scholar-android
./gradlew assembleDebug
```

## APK Output

- Debug: `app/build/outputs/apk/debug/app-debug.apk`
- Release: `app/build/outputs/apk/release/app-release.apk`

## Requirements

- Android SDK 35 (API 35)
- Minimum SDK 24 (Android 7.0)

## Architecture

- **Retrofit 3.0** — HTTP client for API calls
- **Gson** — JSON parsing
- **RecyclerView** — List display
- **Material Design 3** — UI components