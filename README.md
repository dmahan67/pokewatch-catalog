# PokeWatch product catalog

The product list the PokeWatch app downloads. It's a static file, so there is no server to run.

| File | What it is |
| --- | --- |
| `catalog.json` | The list you edit. |
| `catalog.signed.json` | What the app downloads: `catalog.json` plus an Ed25519 signature. **Generated. Don't edit it.** |
| `public-key.txt` | The public key the app trusts (CI uses it too). |
| `scripts/check.py` | CI check: signature valid, file matches, links are on the retailer's own domain. |
| `ci/check.yml` | Optional GitHub Actions workflow that runs the check on every push. Copy it to `.github/workflows/check.yml` to enable it (GitHub needs the `workflow` permission to accept that file). You can also run `python3 scripts/check.py` yourself. |

## Adding or changing items

1. Edit `catalog.json`. Each entry looks like:
   ```json
   {
     "id": "target-1012850570",
     "retailer": "target",
     "tcin": "1012850570",
     "name": "30th Celebration Ultra-Premium Collection- Day",
     "set": "30th Celebration",
     "kind": "Ultra-Premium Collection",
     "suggestedMaxPrice": 119.99,
     "addedAt": "2026-11-08",
     "status": "active"
   }
   ```
   `tcin` is the number in a Target link (`/A-1012850570`). `suggestedMaxPrice` is optional and only a suggestion. Set `"status": "retired"` to hide an item instead of deleting it.
2. From the PokeWatch project folder on your Mac, run `scripts/catalog build`. It validates the file, raises the version, signs it with your private key and writes `catalog.signed.json`.
3. Commit and push both `catalog.json` and `catalog.signed.json`. The app picks up the change the next time it opens (GitHub can take a few minutes to serve the new file).

Because the file is signed on your Mac, editing it from a phone or the GitHub website won't work: an unsigned or changed file is ignored by the app, and CI fails.

## Keys

- The private key is at `~/.pokewatch/catalog-signing.key` on your Mac. It is never committed. **Back it up.** If you lose it you can't publish updates the installed app will accept (you'd ship a new build that trusts a new key).
- Don't run `scripts/catalog keygen --force` unless you mean to replace it.

## Safety rules the app enforces

Product links must be https on the retailer's own domain, ids unique, the version only goes up, and catalog items are only ever added to the watchlist **disarmed**. A catalog can suggest a price but never set one for you.
