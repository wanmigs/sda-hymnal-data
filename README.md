# SDA Hymnal Data

This repository stores hymn and song data for the SDA Hymnal app. It is the **source of truth** for in-app content: lyrics, metadata, and related collections. Changes here are versioned with Git so the app can ship updated data when this repo changes.

## Purpose

- **Data storage** — JSON files hold hymnals, language editions, and supplemental song lists used by the app.
- **Versioning** — Git history tracks what changed, when, and why, so data updates can be reviewed and released deliberately.
- **App updates** — When content is corrected or expanded, update the JSON here, tag or release as your workflow defines, and point the app (or its build/bundle step) at the new revision so users get fresh data without changing app code.

This repo is **data only**; it does not contain the mobile or web app itself.

## Data files

| File | Description |
|------|-------------|
| `english.json` | English hymns (app schema: verses, optional refrain) |
| `tagalog.json` | Tagalog hymns |
| `cebuano.json` | Cebuano hymns |
| `sdahymnal.json` | SDA hymnal entries (stanza-based schema) |
| `scripture-songs.json` | Scripture-based songs |
| `data.json` | Scripture songs grouped by theme/category |
| `ay-songs.json` | Adventist Youth (AY) songs |
| `special-songs.json` | Special / supplemental songs |
| `others.json` | Additional songs not in the main collections |

## Schemas

Most language and supplemental files use a shared **app** shape: an array of songs with `pageNumber`, `title`, `language`, `verses` (numbered stanzas with `lines`), and sometimes a `refrain`.

Example (`english.json`, `ay-songs.json`, etc.):

```json
{
  "pageNumber": 1,
  "title": "Song Title",
  "language": "english",
  "verses": [
    { "number": 1, "lines": ["Line one", "Line two"] }
  ],
  "refrain": { "lines": ["Optional chorus lines"] }
}
```

`sdahymnal.json` uses a different structure: `english_hymns` with hymn `number`, `title`, `topical_index`, and `stanza1`–`stanza4` as newline-separated strings.

## Updating content

1. Edit the relevant JSON file(s).
2. Validate JSON (no trailing commas, matching brackets).
3. Commit with a clear message describing the change (e.g. typo fix, new song, language update).
4. Release or reference the new commit/tag from the app’s data sync or bundle process.

## Contributing

Keep edits focused on lyrical or metadata corrections. Prefer small, reviewable commits. Do not commit secrets or app-specific config—only hymn/song data belongs here.
