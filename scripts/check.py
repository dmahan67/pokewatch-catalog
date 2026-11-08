#!/usr/bin/env python3
"""CI check for the PokeWatch catalog repo.

Fails if catalog.json was edited without re-signing, if the signature is invalid, or if the content breaks the
rules the app enforces (https product links on the retailer's own domain, unique ids, sane fields).
Needs: pip install cryptography
"""
import base64, json, re, sys
from urllib.parse import urlparse
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

HOSTS = {"target": ["target.com"], "walmart": ["walmart.com"], "pokemonCenter": ["pokemoncenter.com"]}
errors = []

def fail(msg): errors.append(msg)

source = open("catalog.json", encoding="utf-8").read()
envelope = json.load(open("catalog.signed.json", encoding="utf-8"))
keys = dict(line.strip().split(":", 1) for line in open("public-key.txt") if ":" in line)

if envelope.get("format") != 1: fail("envelope format must be 1")
if envelope.get("payload") != source:
    fail("catalog.signed.json does not match catalog.json. Run scripts/catalog build and commit both files.")
key = keys.get(envelope.get("keyID"))
if not key:
    fail(f"unknown keyID {envelope.get('keyID')!r}")
else:
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(key)).verify(
            base64.b64decode(envelope["signature"]), envelope["payload"].encode("utf-8"))
    except (InvalidSignature, KeyError, ValueError):
        fail("signature is invalid")

catalog = json.loads(source)
if catalog.get("schema") != 1: fail("schema must be 1")
if not isinstance(catalog.get("version"), int) or catalog["version"] < 1: fail("version must be a positive integer")
ids = set()
products = set()
for e in catalog.get("entries", []):
    eid = e.get("id", "")
    def bad(why): fail(f"{eid or '(no id)'}: {why}")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", eid): bad("bad id")
    if eid in ids: bad("duplicate id")
    ids.add(eid)
    retailer = e.get("retailer")
    if retailer not in HOSTS: bad("unknown retailer"); continue
    if not (1 <= len(e.get("name", "").strip()) <= 200): bad("name must be 1-200 characters")
    price = e.get("suggestedMaxPrice")
    if price is not None and not (0 < price < 100000): bad("suggestedMaxPrice out of range")
    tcin = e.get("tcin")
    if tcin is not None and not (retailer == "target" and re.fullmatch(r"\d{5,12}", tcin)): bad("bad tcin")
    url = e.get("url") or (f"https://www.target.com/p/-/A-{tcin}" if tcin else None)
    parsed = urlparse(url or "")
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not any(host == h or host.endswith("." + h) for h in HOSTS[retailer]):
        bad("link must be https on the retailer's own domain")
    if e.get("status") not in ("active", "retired"): bad("status must be active or retired")
    key = (retailer, ("A-" + tcin) if tcin else (url or "").lower())
    if key in products: bad("the same product is listed twice")
    products.add(key)

if errors:
    print("Catalog check failed:")
    for e in errors: print(" -", e)
    sys.exit(1)
print(f"Catalog OK: version {catalog['version']}, {len(catalog['entries'])} entries, signature valid.")
