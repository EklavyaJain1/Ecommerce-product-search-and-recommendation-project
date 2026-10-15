"""Fetch product photography from Wikimedia Commons for the demo catalogue.

Every file committed to this repository must be redistributable, so the fetcher
accepts a candidate only when Commons declares its licence as CC0, Public Domain
or CC BY. ShareAlike, NonCommercial, NoDerivatives, GFDL and fair-use files are
rejected outright: CC BY-SA would impose its own terms on the public repository,
and the others are not free to redistribute.

Two further filters keep the catalogue from filling up with unusable files:

* Relevance. A file title must contain a meaningful word from the search term,
  and titles naming diagrams, artwork, historical scans, damaged goods, evidence
  photos or unrelated events are rejected.
* Weight. Candidates are tried best-first until one downloads inside
  MAX_BYTES, so a stray multi-megabyte PNG cannot bloat the repository.

Accepted files are recorded in data/product-images.json and rendered into
CREDITS.md, so the author, licence and source page of every image can be checked
later. Product types with no acceptable photo are left out and keep the built-in
duotone illustration as a fallback.

Usage:
    python data/fetch_images.py                      # fetch whatever is missing
    python data/fetch_images.py --force              # refetch everything
    python data/fetch_images.py --only "Smart Watch" # retry selected types
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO

from PIL import Image

API = "https://commons.wikimedia.org/w/api.php"
# Wikimedia asks for a descriptive User-Agent that identifies the tool.
UA = "ShopMind-demo-image-fetch/1.0 (local demo; python-urllib)"

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "static" / "products"
MANIFEST = ROOT / "data" / "product-images.json"
CREDITS = ROOT / "CREDITS.md"

THUMB_WIDTH = 640
MIN_SOURCE_WIDTH = 640
MIN_SOURCE_HEIGHT = 480
MAX_BYTES = 150 * 1024

# Commons throttles bursts; one request at a time with a minimum gap, plus
# backoff on 429/5xx, keeps the fetch inside its limits.
MIN_INTERVAL = 1.1
_last_call = [0.0]

# A title carrying any of these is not product photography of the thing the
# catalogue is selling. Rejecting them outright is the difference between a
# storefront and a scrapbook of whatever the search happened to surface.
BAD_TITLE_WORDS = (
    # diagrams and artwork rather than photographs
    "drawing", "diagram", "layout", "sketch", "illustration", "clipart",
    "logo", "icon", "chart", "graph", "map", "plan", "blueprint", "poster",
    "painting", "engraving", "lithograph", "stamp", "banknote", "postcard",
    "screenshot", "document", "scan", "coat of arms",
    # damaged, historical or institutional subjects
    "shattered", "broken", "damaged", "ruins", "cemetery", "grave", "antique",
    "museum", "statue", "excavation", "archaeolog", "1 8 9", "1 9 0 0",
    # evidence, crime and news photos
    "evidence", "police", "crime", "seized", "confiscat", "efta", "routh",
    "gun", "rifle", "weapon", "arrest", "court", "victim",
    # unrelated events and subjects
    "fundraiser", "protest", "parade", "festival", "cake", "pie in the face",
    "wedding", "funeral", "tattoo", "x-ray", "radiograph", "microscope",
    # the wrong product
    "remover", "empty bottle", "packaging", "carton", "label", "receipt",
    "instructions", "manual",
    # landmarks and oddities that happen to share a name with a product
    "largest", "landmark", "school bag", "spoon on", "lca of",
)

# Patterns that mark a file as artwork or a museum object rather than product
# photography: artist life dates in the title, or an accession number.
BAD_TITLE_PATTERNS = (
    r"\b1[5-9]\d{2}\s*[-\u2013]\s*1[89]\d{2}\b",
    r"\(\s*am\s*\d",
    r"\bam\s+\d{6}\b",
)

# Search phrase per catalogue product type. Book titles in the catalogue are
# fictional, so book types map to a generic physical-book photograph.
QUERIES = {
    # Electronics
    "4K Streaming Stick": "streaming media player",
    "Bluetooth Speaker": "bluetooth speaker",
    "Full HD Webcam": "webcam",
    "Gaming Mouse": "computer mouse",
    "Laptop Stand": "laptop stand",
    "LED Table Lamp": "desk lamp",
    "Mechanical Keyboard": "computer keyboard",
    "Noise-Cancelling Headphones": "headphones",
    "Power Bank 20000mAh": "power bank battery",
    "Robot Vacuum": "robot vacuum cleaner",
    "Smart Watch": "smartwatch",
    "Wireless Earbuds": "wireless earbuds",
    # Fashion
    "Canvas Backpack": "backpack",
    "Chronograph Watch": "wristwatch",
    "Denim Jacket": "denim jacket",
    "Everyday Sneakers": "sneakers shoes",
    "Floral Summer Dress": "summer dress",
    "Leather Jacket": "leather jacket clothing",
    "Merino Wool Scarf": "wool scarf",
    "Organic Cotton T-Shirt": "t-shirt clothing",
    "Polarized Sunglasses": "sunglasses",
    "Slim Denim Jeans": "denim jeans",
    "Trail Running Shoes": "running shoes",
    # Home & Kitchen
    "2-Person Camping Tent": "camping tent",
    "40L Hiking Backpack": "hiking backpack rucksack",
    "Adjustable Dumbbell Set": "dumbbell weights",
    "Cast Iron Skillet": "cast iron skillet",
    "Ceramic Dinnerware Set": "porcelain plate",
    "Chunky Knit Throw Blanket": "knitted wool blanket",
    "Cycling Helmet": "bicycle helmet cycling",
    "Digital Air Fryer": "air fryer",
    "Espresso Machine": "espresso machine",
    "Insulated Water Bottle": "water bottle",
    "Memory Foam Pillow": "bed pillow",
    "Non-Slip Yoga Mat": "yoga mat rolled",
    "Nonstick Frying Pan": "frying pan cookware",
    "Resistance Bands Set": "resistance band",
    "Soy Wax Candle": "candle",
    "Speed Skipping Rope": "jump rope",
    # Beauty
    "Argan Oil Shampoo": "shampoo bottle",
    "Daily Face Moisturizer": "face cream",
    "Eau de Parfum": "perfume bottle",
    "Gel Nail Lacquer Set": "nail polish bottle",
    "Ionic Hair Dryer": "hair dryer",
    "Matte Liquid Lipstick": "lipstick",
    "Mineral Sunscreen SPF 50": "sunscreen lotion",
    "Vitamin C Face Serum": "serum bottle cosmetic",
    # Books
    "Biography: The Bridge Builder": "hardcover book",
    "Business: Lean Momentum": "business book",
    "Fantasy Trilogy: Ash & Crown": "fantasy book cover",
    "Mystery Novel: The Silent Harbor": "mystery novel book",
    "Poetry: Saltwater Lines": "poetry book",
    "Sci-Fi Epic: Signals from Vega": "science fiction novel",
    "Self-Help: Focus Formula": "book cover",
    "The Weeknight Cookbook": "cookbook",
}

# A real book cover would misrepresent a title this catalogue invented, and a
# single generic cover repeated across 24 book listings reads worse than the
# three illustration variants the front end already draws. Book types therefore
# keep their illustrations on purpose.
SKIP_TYPES = {
    "Biography: The Bridge Builder",
    "Business: Lean Momentum",
    "Fantasy Trilogy: Ash & Crown",
    "Mystery Novel: The Silent Harbor",
    "Poetry: Saltwater Lines",
    "Sci-Fi Epic: Signals from Vega",
    "Self-Help: Focus Formula",
    "The Weeknight Cookbook",
}

REJECT_LICENCE = ("gfdl", "fal", "fair use", "non-free", "nonfree")
# Free to redistribute, but they carry obligations this repository does not want.
REJECT_CLAUSES = ("-sa", "-nc", "-nd")


def normalise(payload: bytes) -> bytes:
    """Re-encode to a web-sized JPEG.

    Commons serves whatever format the source used, and a 640px thumbnail of a
    transparent PNG can still run to hundreds of kilobytes. Normalising keeps
    the repository small and gives the storefront one predictable format.
    """
    with Image.open(BytesIO(payload)) as image:
        image = image.convert("RGB")
        if image.width > THUMB_WIDTH:
            ratio = THUMB_WIDTH / image.width
            image = image.resize(
                (THUMB_WIDTH, max(1, round(image.height * ratio))), Image.LANCZOS
            )
        out = BytesIO()
        image.save(out, "JPEG", quality=80, optimize=True, progressive=True)
        return out.getvalue()


def api(params: dict, attempts: int = 5) -> dict:
    """GET the Commons API, pacing requests and backing off when throttled."""
    query = dict(params)
    query["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(query)
    delay = 4.0
    for attempt in range(1, attempts + 1):
        gap = MIN_INTERVAL - (time.monotonic() - _last_call[0])
        if gap > 0:
            time.sleep(gap)
        request = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            _last_call[0] = time.monotonic()
            return payload
        except urllib.error.HTTPError as exc:
            _last_call[0] = time.monotonic()
            if not (exc.code == 429 or 500 <= exc.code < 600) or attempt == attempts:
                raise
            header = exc.headers.get("Retry-After") if exc.headers else None
            pause = float(header) if (header or "").strip().isdigit() else delay
            print(f"    throttled ({exc.code}); retry {attempt}/{attempts - 1} in {pause:.0f}s")
            time.sleep(pause)
            delay = min(delay * 2, 45.0)
    raise RuntimeError("api: exhausted attempts")


def strip_tags(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", text).strip()


def licence_ok(short: str, licence_url: str = "") -> bool:
    """True only for CC0, Public Domain and plain CC BY."""
    low = (short or "").strip().lower()
    url = (licence_url or "").lower()
    if not low and not url:
        return False
    if any(bad in low for bad in REJECT_LICENCE):
        return False
    flat = low.replace(" ", "-")
    if any(clause in flat for clause in REJECT_CLAUSES):
        return False
    if "/publicdomain/" in url or "/zero/" in url:
        return True
    if low.startswith("cc0") or "public domain" in low or low in {"pd", "pd-us", "pd-old"}:
        return True
    return bool(re.match(r"^cc[ -]?by(?![- ]?(sa|nc|nd))", flat))


def relevance(title: str, term: str) -> int:
    """Positive when a meaningful word of the term appears in the file title."""
    title = title or ""
    low = title.lower()
    if any(bad in low for bad in BAD_TITLE_WORDS):
        return -1
    if any(re.search(pattern, low) for pattern in BAD_TITLE_PATTERNS):
        return -1
    return sum(1 for token in re.findall(r"[a-z]+", term.lower()) if len(token) > 3 and token in low)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "image"


def search_candidates(term: str) -> list:
    data = api(
        {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {term}",
            "gsrnamespace": "6",
            "gsrlimit": "24",
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
            "iiurlwidth": str(THUMB_WIDTH),
        }
    )
    pages = (data.get("query") or {}).get("pages") or {}
    return sorted(pages.values(), key=lambda p: p.get("index", 0))


def rank(pages: list, term: str) -> list:
    """Acceptable candidates, best title match first."""
    accepted = []
    rejected = 0
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        short = (meta.get("LicenseShortName") or {}).get("value", "")
        licence_url = (meta.get("LicenseUrl") or {}).get("value", "")
        if not licence_ok(short, licence_url):
            rejected += 1
            continue
        if (info.get("width") or 0) < MIN_SOURCE_WIDTH or (info.get("height") or 0) < MIN_SOURCE_HEIGHT:
            rejected += 1
            continue
        if not info.get("thumburl"):
            rejected += 1
            continue
        score = relevance(page.get("title", ""), term)
        if score < 1:
            rejected += 1
            continue
        accepted.append(
            {
                "score": score,
                "index": page.get("index", 0),
                "title": page.get("title", ""),
                "info": info,
                "short": short,
                "licence_url": licence_url,
                "author": strip_tags((meta.get("Artist") or {}).get("value", "")) or "Unknown",
            }
        )
    accepted.sort(key=lambda c: (-c["score"], c["index"]))
    return accepted, rejected


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def write_credits(manifest: dict) -> None:
    rows = sorted(manifest.items(), key=lambda kv: kv[0].lower())
    lines = [
        "# Image credits",
        "",
        "Product photography in this project comes from Wikimedia Commons. Only files whose",
        "Commons-declared licence is **CC0**, **Public Domain** or **CC BY** are used. Files",
        "under ShareAlike, NonCommercial, NoDerivatives, GFDL or fair use were rejected, so",
        "nothing here imposes additional terms on this repository.",
        "",
        f"Regenerate with `python data/fetch_images.py`. {len(rows)} product type(s) have a",
        "photo; any type without one falls back to the built-in duotone illustration.",
        "",
        "Book types are left to the illustrations deliberately: a real cover would suggest",
        "a title the catalogue invented.",
        "",
        "| Product type | File | Author | Licence | Source |",
        "| --- | --- | --- | --- | --- |",
    ]
    for product_type, meta in rows:
        author = (meta.get("author") or "Unknown").replace("|", "/")
        lines.append(
            f"| {product_type} | `{meta['file']}` | {author} | {meta['license']} "
            f"| [Commons]({meta['source']}) |"
        )
    lines.append("")
    CREDITS.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="refetch images that already exist")
    ap.add_argument("--only", default="", help="comma-separated product types to process")
    ap.add_argument("--limit", type=int, default=0, help="only process the first N types")
    args = ap.parse_args()

    # File titles are not always ASCII; never let a print kill the run.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    if args.force:
        # A forced run re-decides every type, so stale picks are not carried over.
        for stale in OUT_DIR.glob("*"):
            if stale.is_file():
                stale.unlink()
        print("force: cleared existing images and manifest")
    elif MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    if not args.only:
        # Retire any photo that should not be shipped, including books fetched by
        # an earlier version of this script.
        for product_type in sorted(SKIP_TYPES):
            old = manifest.pop(product_type, None)
            if old:
                stale = OUT_DIR / pathlib.Path(old["file"]).name
                if stale.exists():
                    stale.unlink()

    targets = [(t, q) for t, q in QUERIES.items() if t not in SKIP_TYPES]
    if args.only:
        wanted = {t.strip() for t in args.only.split(",") if t.strip()}
        unknown = wanted - set(QUERIES)
        if unknown:
            print(f"unknown type(s): {', '.join(sorted(unknown))}")
            return 2
        targets = [(t, QUERIES[t]) for t in QUERIES if t in wanted]
        # A targeted retry replaces its previous pick, so a type that finds
        # nothing better falls back to the illustration rather than silently
        # keeping a known-bad image.
        for product_type, _ in targets:
            old = manifest.pop(product_type, None)
            if old:
                stale = OUT_DIR / pathlib.Path(old["file"]).name
                if stale.exists():
                    stale.unlink()
    elif args.limit:
        targets = targets[: args.limit]

    saved = skipped = failed = 0
    misses = []
    for index, (product_type, term) in enumerate(targets, 1):
        existing = manifest.get(product_type)
        if existing and not args.force:
            if (OUT_DIR / pathlib.Path(existing["file"]).name).exists():
                skipped += 1
                continue

        try:
            candidates, rejected = rank(search_candidates(term), term)
        except Exception as exc:
            print(f"[{index:>2}] {product_type}: search failed ({exc})")
            failed += 1
            continue

        if not candidates:
            misses.append((product_type, f"no usable CC0/CC BY photo ({rejected} rejected)"))
            print(f"[{index:>2}] {product_type}: no usable image ({rejected} rejected)")
            continue

        chosen = None
        for candidate in candidates:
            thumb = candidate["info"]["thumburl"]
            try:
                payload = normalise(download(thumb))
            except Exception as exc:
                print(f"    {candidate['title'][:48]}: unusable ({exc})")
                continue
            if len(payload) > MAX_BYTES:
                print(
                    f"    {candidate['title'][:48]}: {len(payload) // 1024} KB over budget, trying next"
                )
                continue
            chosen = (candidate, payload)
            break

        if not chosen:
            misses.append((product_type, "no candidate within size budget"))
            print(f"[{index:>2}] {product_type}: nothing within size budget")
            continue

        candidate, payload = chosen
        filename = f"{slugify(product_type)}.jpg"
        (OUT_DIR / filename).write_bytes(payload)
        manifest[product_type] = {
            "file": f"products/{filename}",
            "bytes": len(payload),
            "title": candidate["title"],
            "author": candidate["author"],
            "license": candidate["short"],
            "licenseUrl": candidate["licence_url"],
            "source": candidate["info"].get("descriptionurl", ""),
        }
        saved += 1
        print(
            f"[{index:>2}] {product_type}: {candidate['short']:<14} {len(payload) // 1024:>4} KB  "
            f"{candidate['title'][:46]}"
        )

    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_credits(manifest)

    total_kb = sum(m["bytes"] for m in manifest.values()) // 1024
    print()
    print(f"saved {saved}, already present {skipped}, failed {failed}, no image {len(misses)}")
    print(f"manifest: {MANIFEST.relative_to(ROOT)}  ({len(manifest)} entries, {total_kb} KB on disk)")
    if misses:
        print("types without a photo:")
        for product_type, why in misses:
            print(f"  - {product_type}: {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
