#!/usr/bin/env python3
"""
Regenerate manifest.json from all hymn/song data files in the repo root.

Run after editing any collection JSON:
  python3 scripts/update-manifest.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "manifest.json"

# Default appVersion used only when manifest.json does not already define one.
# Edit appVersion directly in manifest.json; regeneration preserves that value.
DEFAULT_APP_VERSION = "1.0.0"

# Stable catalog order and metadata (edit here when adding a new collection file).
COLLECTION_SPECS = [
    {
        "id": "english",
        "file": "english.json",
        "title": "English Hymns",
        "description": "English hymns (app schema: verses, optional refrain).",
        "schema": "app",
    },
    {
        "id": "tagalog",
        "file": "tagalog.json",
        "title": "Tagalog Hymns",
        "description": "Tagalog hymns (app schema).",
        "schema": "app",
    },
    {
        "id": "cebuano",
        "file": "cebuano.json",
        "title": "Cebuano Hymns",
        "description": "Cebuano hymns (app schema).",
        "schema": "app",
    },
    {
        "id": "sdahymnal",
        "file": "sdahymnal.json",
        "title": "SDA Hymnal",
        "description": "SDA hymnal entries (stanza-based schema).",
        "schema": "sdahymnal",
    },
    {
        "id": "scripture-songs",
        "file": "scripture-songs.json",
        "title": "Scripture Songs",
        "description": "Scripture-based songs (app schema).",
        "schema": "app",
    },
    {
        "id": "data",
        "file": "data.json",
        "title": "Scripture Songs (Themed & Full Lyrics)",
        "description": "Themed scripture song snippets and full-lyrics collection.",
        "schema": "composite",
    },
    {
        "id": "ay-songs",
        "file": "ay-songs.json",
        "title": "Adventist Youth Songs",
        "description": "Adventist Youth (AY) songs (app schema).",
        "schema": "app",
    },
    {
        "id": "special-songs",
        "file": "special-songs.json",
        "title": "Special Songs",
        "description": "Special and supplemental songs (app schema).",
        "schema": "app",
    },
    {
        "id": "others",
        "file": "others.json",
        "title": "Other Content",
        "description": "Additional structured content (e.g. Ten Commandments).",
        "schema": "structured",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_documents(path: Path) -> list[object]:
    raw = path.read_text(encoding="utf-8")
    documents: list[object] = []
    decoder = json.JSONDecoder()
    index = 0
    while index < len(raw):
        while index < len(raw) and raw[index].isspace():
            index += 1
        if index >= len(raw):
            break
        document, end = decoder.raw_decode(raw, index)
        documents.append(document)
        index = end
    if not documents:
        raise ValueError(f"{path.name}: empty or invalid JSON")
    return documents


def analyze_app_array(data: list) -> dict:
    return {"count": len(data)}


def analyze_sdahymnal(data: dict) -> dict:
    hymns = data.get("english_hymns", [])
    return {"count": len(hymns), "rootKey": "english_hymns"}


def analyze_structured(data: list) -> dict:
    return {"count": len(data)}


def analyze_data_file(documents: list[object]) -> dict:
    parts = []
    total_count = 0
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            raise ValueError(f"data.json part {index}: expected object")
        if "scripture_songs" in document:
            categories = document["scripture_songs"]
            song_count = sum(
                len(items) for items in categories.values() if isinstance(items, list)
            )
            total_count += song_count
            parts.append(
                {
                    "part": index,
                    "rootKey": "scripture_songs",
                    "schema": "scripture-themed",
                    "categoryCount": len(categories),
                    "count": song_count,
                }
            )
        elif "full_lyrics_collection" in document:
            items = document["full_lyrics_collection"]
            count = len(items) if isinstance(items, list) else 0
            total_count += count
            parts.append(
                {
                    "part": index,
                    "rootKey": "full_lyrics_collection",
                    "schema": "full-lyrics",
                    "count": count,
                }
            )
        else:
            raise ValueError(
                f"data.json part {index}: unknown root keys {list(document.keys())}"
            )
    return {"count": total_count, "parts": parts}


def analyze_collection(spec: dict, path: Path) -> dict:
    documents = load_json_documents(path)
    schema = spec["schema"]
    entry: dict = {
        "id": spec["id"],
        "file": spec["file"],
        "title": spec["title"],
        "description": spec["description"],
        "schema": schema,
        "sha256": sha256_file(path),
        "sizeBytes": path.stat().st_size,
    }

    if schema == "app":
        if len(documents) != 1 or not isinstance(documents[0], list):
            raise ValueError(f"{path.name}: app schema expects a single JSON array")
        entry.update(analyze_app_array(documents[0]))
    elif schema == "sdahymnal":
        if len(documents) != 1 or not isinstance(documents[0], dict):
            raise ValueError(f"{path.name}: sdahymnal schema expects a single JSON object")
        entry.update(analyze_sdahymnal(documents[0]))
    elif schema == "structured":
        if len(documents) != 1 or not isinstance(documents[0], list):
            raise ValueError(f"{path.name}: structured schema expects a single JSON array")
        entry.update(analyze_structured(documents[0]))
    elif schema == "composite":
        if spec["file"] != "data.json":
            raise ValueError("composite schema is only defined for data.json")
        entry.update(analyze_data_file(documents))
    else:
        raise ValueError(f"unknown schema {schema!r}")

    return entry


def content_version(collections: list[dict]) -> str:
    combined = "".join(item["sha256"] for item in collections)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]


def read_existing_app_version() -> str:
    """Preserve a manually-edited appVersion across regenerations."""
    if not MANIFEST_PATH.is_file():
        return DEFAULT_APP_VERSION
    try:
        existing = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_APP_VERSION
    app_version = existing.get("appVersion")
    if isinstance(app_version, str) and app_version.strip():
        return app_version
    return DEFAULT_APP_VERSION


def build_manifest() -> dict:
    collections = []
    for spec in COLLECTION_SPECS:
        path = REPO_ROOT / spec["file"]
        if not path.is_file():
            raise FileNotFoundError(f"Missing data file: {path}")
        collections.append(analyze_collection(spec, path))

    return {
        "manifestVersion": 1,
        "appVersion": read_existing_app_version(),
        "contentVersion": content_version(collections),
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collections": collections,
    }


def main() -> int:
    try:
        manifest = build_manifest()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"update-manifest: {error}", file=sys.stderr)
        return 1

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {MANIFEST_PATH.relative_to(REPO_ROOT)}")
    print(f"  appVersion:     {manifest['appVersion']}")
    print(f"  contentVersion: {manifest['contentVersion']}")
    print(f"  collections:    {len(manifest['collections'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
