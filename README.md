# ecomadsfix.com

Static site in three languages (EN at root, `/uk/`, `/ru/`), deployed on Cloudflare Workers from the `public/` folder.

## Editing

- Pages: `src/pages/<lang>/...html` (JSON meta block on top, HTML body below).
- Telegram, author name and photo: `src/config.json`.
- Cases with screenshots: `src/cases.json` + images in `src/static/img/cases/`. A case appears on every guide whose `topic` matches (`suspension`, `misrepresentation`, `mismatch`, `not-showing`, `pmax`, `tracking`).
- Styles: `src/static/style.css`. Old URLs → new: `src/static/_redirects`.

After any change run `python3 build.py` and commit `public/` together with `src/`.
Cloudflare doesn't build anything: it publishes `public/` as is (see `wrangler.jsonc`).

Case format:

```json
{
  "topic": "misrepresentation",
  "images": [{"file": "case1-before.png", "w": 1200, "h": 700, "alt": {"en": "...", "uk": "...", "ru": "..."}}],
  "text": {
    "en": {"title": "...", "cause": "...", "fix": "...", "result": "..."},
    "uk": {"title": "...", "cause": "...", "fix": "...", "result": "..."},
    "ru": {"title": "...", "cause": "...", "fix": "...", "result": "..."}
  }
}
```
