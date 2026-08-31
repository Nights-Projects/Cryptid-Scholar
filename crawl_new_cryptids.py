#!/usr/bin/env python3  # noqa: EXE001
"""
Cryptid Data Updater — crawls Wikipedia's "List of cryptids" page,
compares against existing seed data, and produces a detailed diff report.

Features:
  - Detects truly NEW cryptids (name not in seed)
  - Detects UPDATED cryptids (same name, new/changed data)
  - Detects ENRICHED cryptids (existing entry missing fields that Wikipedia has)
  - Produces no_duplicate JSON output for review before merging

Usage:
  python3 crawl_new_cryptids.py                    # crawl + write diff report
  python3 crawl_new_cryptids.py --dry-run          # preview diff only
  python3 crawl_new_cryptids.py --apply            # apply updates to seed in-place
"""

import argparse
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_cryptids"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CryptidScholar/1.0; +https://github.com/NicSparks/cryptid-scholar)"
}
SEED_PATH = Path(__file__).resolve().parent / "cryptids_seed.json"
DIFF_REPORT_PATH = Path(__file__).resolve().parent / "crawl_diff_report.json"

# Blacklist — Wikipedia nav links / categories / disambiguation junk
NAV_BLACKLIST = {
    "main page", "contents", "current events", "random article", "about wikipedia",
    "help", "learn to edit", "community portal", "recent changes", "upload file",
    "special pages", "cryptids", "lists of legendary creatures",
    "articles with short description", "short description is different from wikidata",
    "wikipedia indefinitely semi-protected pages", "use dmy dates from june 2020",
    "cs1 spanish-language sources (es)", "all articles with unsourced statements",
    "articles with unsourced statements from march 2023",
    "articles with unsourced statements from april 2026",
    "cs1 interwiki-linked names", "commons link is locally defined",
    "creative commons attribution-sharealike 4.0 license", "disclaimers",
    "categories", "portal", "wiki", "free media", "privacy policy",
    "wikipedia:", "template:", "category:", "file:", "help:", "special:",
    "media:", "book:", "mos:", "portal:", "draft:", "timedtext:",
}

KNOWN_AQUATIC = ["loch", "ness", "champ", "ogopogo", "bunyip", "mokele", "morag",
                 "muckleshoot", "chessie", "each-uisge", "kelpie", "selkie",
                 "nokk", "nøkken", "rusalka", "merrow", "mami wata", "kraken",
                 "sea serpent", "basilisk", "hydra", "st. augustine", "king hoo",
                 "megalania", "caddy", "water", "lake", "river", "sea monster",
                 "mermaid", "siren"]
KNOWN_FLYING = ["jersey devil", "mothman", "roc", "thunderbird", "bat",
                "vampire", "striga", "barghest", "flying", "harpy", "lamia",
                "strzyga", "aswang", "penanggalan"]


def fetch_wiki_page(url: str, retries: int = 3) -> str | None:
    """Fetch Wikipedia page HTML with retry logic."""
    last_error = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            last_error = e
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"[!] Attempt {attempt + 1} failed: {e} — retrying in {wait}s")
                time.sleep(wait)
    # All retries exhausted - return None after the loop
    print(f"[!] All retries failed for {url}: {last_error}")
    return None


def is_real_cryptid(name: str) -> bool:
    """Filter out navigation, category, disambiguation, and non-cryptid entries."""
    if not name or len(name) < 3:
        return False
    name_lower = name.lower().strip()

    if name_lower in NAV_BLACKLIST:
        return False
    if "List_" in name or "list of" in name_lower:
        return False
    if "category:" in name_lower or "template:" in name_lower:
        return False
    if ":" in name and "wikipedia" not in name_lower:
        return False

    # Filter out non-individual cryptids and overly generic entries
    non_individual = [
        "cryptid whales", "sea serpents", "phantom kangaroo", "giant (afghanistan)",
        "megalodon (surviving", "moa (surviving", "thylacine (surviving",
        "homo floresiensis (surviving", "manatee (surviving", "marsupial lion (surviving",
        "passenger pigeon (surviving", "wisent (surviving", "aurochs (surviving",
        "cave lion (surviving", "sabretooth (surviving", "mammoth (surviving",
        "irish elk (surviving", "woolly rhinoceros (surviving", "steppe bison (surviving",
    ]
    for item in non_individual:
        if item in name_lower:
            return False

    # Filter out overly generic single-word entries that aren't specific cryptids
    if name_lower in ("mermaid", "giant", "monster", "beast", "creature"):
        return False

    return True


def extract_image_from_cell(cell) -> str:
    """Extract the highest-res image URL from a table cell."""
    img_tag = cell.find("img")
    if not img_tag:
        return ""
    srcset = img_tag.get("srcset", "")
    if srcset:
        entries = srcset.split(", ")
        for entry in reversed(entries):
            parts = entry.strip().split(" ")
            if parts:
                url = parts[0]
                if url.startswith("//"):
                    url = "https:" + url
                return url
        return "https:" + entries[0].split(" ")[0]
    src = img_tag.get("src", "")
    if src.startswith("//"):
        src = "https:" + src
    return src


def infer_type(name: str, context: str = "") -> str:
    """Infer cryptid type from name and surrounding context."""
    combined = (name + " " + context).lower()
    if any(k in combined for k in KNOWN_AQUATIC):
        return "aquatic"
    if any(k in combined for k in KNOWN_FLYING):
        return "flying"
    return "terrestrial"


def parse_cryptid_tables(soup: BeautifulSoup) -> list[dict]:
    """Parse all wikitable elements in the article content for cryptid entries."""
    cryptids = []

    content = soup.find("div", {"class": "mw-content-ltr", "lang": True})
    if not content:
        content = soup.find("div", id="mw-content-text")
    if not content:
        content = soup

    tables = content.find_all("table", class_="wikitable")
    print(f"[*] Found {len(tables)} wikitable(s) in article content")

    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:
            # Include both th and td (Wikipedia sometimes uses th for first column)
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            name_cell = cells[0]
            name_link = name_cell.find("a", href=lambda x: x and ("wiki" in x or x.startswith("/wiki/")) and "List_of" not in x)
            if not name_link:
                continue

            name = name_link.get_text(strip=True)
            # Remove citation brackets like [10], [11] etc.
            name = re.sub(r'\s*\[[\d\w]+\]\s*$', '', name).strip()
            if not is_real_cryptid(name):
                continue

            rel_url = name_link.get("href", "")
            if rel_url.startswith("http"):
                source_url = rel_url
            elif rel_url.startswith("/wiki/"):
                source_url = f"https://en.wikipedia.org{rel_url}"
            else:
                source_url = ""

            # Wikipedia columns: Name, Other names, Description, Purported location, Depiction
            remaining = list(cells[1:])

            other_names = ""
            description = ""
            location = ""
            country = ""

            if len(remaining) >= 1:
                other_names = remaining[0].get_text(" ", strip=True)
            if len(remaining) >= 2:
                description = remaining[1].get_text(" ", strip=True)[:300]
            if len(remaining) >= 3:
                location = remaining[2].get_text(" ", strip=True)[:80]

            # Try to infer country from location
            country = location.split(",")[-1].strip() if location else ""

            image_url = extract_image_from_cell(name_cell)
            cryptid_type = infer_type(name, country + " " + location + " " + description)

            cryptid = {
                "name": name,
                "type": cryptid_type,
                "other_names": other_names,
                "country": country,
                "location": location,
                "description": description,
                "fact": "",
                "tips": "",
                "image_url": image_url,
                "source_url": source_url,
                "cultural_origin": country or "Unknown",
                "first_recorded": "Unknown",
            }
            cryptids.append(cryptid)

    return cryptids


def load_seed(seed_path: Path) -> list[dict]:
    """Load existing seed data."""
    if not seed_path.exists():
        return []
    with open(seed_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_name_index(seed_data: list[dict]) -> dict:
    """Build a lowercased-name index for fast lookup."""
    return {item["name"].lower(): item for item in seed_data}


def compute_diff(wiki_cryptids: list[dict], seed_data: list[dict]) -> dict:
    """Compare crawled Wikipedia data against existing seed.

    Returns:
      {
        "new": [...],        # truly new cryptids not in seed
        "updated": [...],     # existing cryptids with changed data
        "enriched": [...],   # existing cryptids missing fields Wikipedia has
        "unchanged": [...],   # existing cryptids, no changes
        "summary": {counts}
      }
    """
    seed_index = build_name_index(seed_data)
    new = []
    updated = []
    enriched = []
    unchanged = []

    for wiki_item in wiki_cryptids:
        name_lower = wiki_item["name"].lower()
        existing = seed_index.get(name_lower)

        if not existing:
            # Brand new cryptid
            new.append(wiki_item)
            continue

        # Compare each field
        changes = {}
        enrichments = {}

        for field in ["description", "image_url", "source_url", "country",
                       "location", "type", "other_names"]:
            wiki_val = (wiki_item.get(field) or "").strip()
            seed_val = (existing.get(field) or "").strip()

            # Enrichment: seed has empty, wiki has data
            if not seed_val and wiki_val:
                enrichments[field] = {"from": seed_val, "to": wiki_val}

            # Update: both have different non-empty values
            if seed_val and wiki_val and seed_val != wiki_val:
                should_update = False

                if field == "image_url":
                    # Always update image_url if different
                    should_update = True
                elif field == "source_url":
                    # Always update source_url
                    should_update = True
                elif field == "type":
                    # Use Wikipedia's type if it's more specific
                    if wiki_val != "terrestrial" and seed_val == "terrestrial":
                        should_update = True
                    elif wiki_val == "terrestrial" and seed_val != "terrestrial":
                        should_update = False  # Keep our better classification
                elif field in ("description", "country", "location", "other_names"):
                    # For text fields, prefer the longer/more detailed version
                    if len(wiki_val) > len(seed_val):
                        should_update = True

                if should_update:
                    changes[field] = {"from": seed_val, "to": wiki_val}

        # Also check newly added fields (cultural_origin, first_recorded)
        for field in ["cultural_origin", "first_recorded"]:
            wiki_val = (wiki_item.get(field) or "").strip()
            seed_val = (existing.get(field) or "").strip()
            if not seed_val and wiki_val:
                enrichments[field] = {"from": seed_val, "to": wiki_val}

        if changes or enrichments:
            entry = {
                "name": wiki_item["name"],
                "changes": changes,
                "enrichments": enrichments,
                "seed_record": existing,
                "wiki_record": wiki_item
            }
            if changes:
                updated.append(entry)
            elif enrichments:
                enriched.append(entry)
        else:
            unchanged.append({"name": wiki_item["name"], "seed": existing})

    return {
        "new": new,
        "updated": updated,
        "enriched": enriched,
        "unchanged": unchanged,
        "summary": {
            "total_found": len(wiki_cryptids),
            "new_count": len(new),
            "updated_count": len(updated),
            "enriched_count": len(enriched),
            "unchanged_count": len(unchanged),
            "seed_total": len(seed_data)
        }
    }


def apply_diff(diff: dict, seed_path: Path) -> dict:
    """Apply the diff to the seed JSON file in-place."""
    seed_data = load_seed(seed_path)
    seed_index = build_name_index(seed_data)

    # Add new cryptids
    for item in diff["new"]:
        seed_data.append(item)
        seed_index[item["name"].lower()] = item

    # Apply updates and enrichments
    for entry in diff["updated"] + diff["enriched"]:
        name_lower = entry["name"].lower()
        existing = seed_index.get(name_lower)
        if not existing:
            # Shouldn't happen, but just in case
            continue

        all_changes = {**entry["enrichments"], **entry["changes"]}
        for field, change in all_changes.items():
            existing[field] = change["to"]

    # Write back
    with open(seed_path, "w", encoding="utf-8") as f:
        json.dump(seed_data, f, ensure_ascii=False, indent=2)

    return {"applied": True, "new_count": len(diff["new"]),
            "updated_count": len(diff["updated"]),
            "enriched_count": len(diff["enriched"]),
            "new_total": len(seed_data)}


def main():
    parser = argparse.ArgumentParser(description="Crawl Wikipedia and diff against seed data")
    parser.add_argument("--dry-run", action="store_true", help="Preview diff only — no files written")
    parser.add_argument("--apply", action="store_true", help="Apply updates directly to cryptids_seed.json")
    args = parser.parse_args()

    # Load existing seed
    seed_data = load_seed(SEED_PATH)
    print(f"[*] Loaded {len(seed_data)} cryptids from seed data")

    # Fetch Wikipedia
    print(f"[*] Fetching {WIKI_URL}...")
    html = fetch_wiki_page(WIKI_URL)
    if not html:
        print("[!] Failed to fetch Wikipedia page")
        return

    soup = BeautifulSoup(html, "html.parser")
    wiki_cryptids = parse_cryptid_tables(soup)
    print(f"[*] Found {len(wiki_cryptids)} cryptids on Wikipedia")

    # Compute diff
    diff = compute_diff(wiki_cryptids, seed_data)
    summary = diff["summary"]
    print("\n[*] Diff Summary:")
    print(f"    Total found on Wikipedia: {summary['total_found']}")
    print(f"    New (not in seed):        {summary['new_count']}")
    print(f"    Updated (changed data):   {summary['updated_count']}")
    print(f"    Enriched (new fields):    {summary['enriched_count']}")
    print(f"    Unchanged:                {summary['unchanged_count']}")

    # Show new cryptids
    if diff["new"]:
        print("\n[+] New cryptids found:")
        for c in diff["new"]:
            print(f"  • {c['name']} ({c['country'] or '?'}) — {c['type']}")

    # Show updated cryptids
    if diff["updated"]:
        print("\n[~] Updated cryptids:")
        for entry in diff["updated"][:10]:  # show first 10
            print(f"  • {entry['name']}:")
            for field, change in list(entry["changes"].items())[:3]:
                old = change["from"][:60] + "..." if len(change["from"]) > 60 else change["from"]
                print(f"      {field}: \"{old}\" → \"{change['to'][:60]}...\"")

    # Show enriched cryptids
    if diff["enriched"]:
        print("\n[+] Enriched cryptids (new fields added):")
        for entry in diff["enriched"][:10]:
            print(f"  • {entry['name']}: {', '.join(entry['enrichments'].keys())}")

    # Write diff report
    if not args.dry_run:
        with open(DIFF_REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(diff, f, ensure_ascii=False, indent=2)
        print(f"\n[✓] Full diff report written to {DIFF_REPORT_PATH}")

        if args.apply:
            result = apply_diff(diff, SEED_PATH)
            print(f"\n[✓] Changes applied to seed: {result}")
            print(f"    New total: {result['new_total']} cryptids")
        else:
            print("\n[!] To apply: python3 crawl_new_cryptids.py --apply")
    else:
        print("\n[*] Dry run — no files written")

    if not args.dry_run and not args.apply:
        print("[!] To apply updates: python3 crawl_new_cryptids.py --apply")
        print("[!] To preview:      python3 crawl_new_cryptids.py --dry-run")


if __name__ == "__main__":
    main()