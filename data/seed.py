"""Deterministic product catalog generator -> data/products.json
Run: python data/seed.py
"""
import json
import math
import random
from pathlib import Path

random.seed(42)

# category -> list of product type dicts
CATALOG = {
    "Electronics": {
        "brands": ["Soniq", "Nexpure", "Voltique", "AeroTech", "Pixelon"],
        "types": [
            ("Wireless Earbuds", "\U0001F3A7", ["wireless", "bluetooth", "noise-isolating", "case", "audio"], (29, 199)),
            ("Smart Watch", "⌚", ["fitness", "heart-rate", "amoled", "water-resistant", "notifications"], (59, 329)),
            ("Bluetooth Speaker", "\U0001F50A", ["portable", "bass", "waterproof", "battery", "audio"], (24, 149)),
            ("4K Streaming Stick", "\U0001F4FA", ["4k", "hdr", "streaming", "voice-remote", "tv"], (34, 79)),
            ("Mechanical Keyboard", "⌨️", ["mechanical", "rgb", "hot-swappable", "usb-c", "gaming"], (69, 219)),
            ("Gaming Mouse", "\U0001F5B1️", ["ergonomic", "dpi", "rgb", "wireless", "gaming"], (29, 129)),
            ("Power Bank 20000mAh", "\U0001F50B", ["charging", "fast-charge", "usb-c", "portable", "battery"], (19, 69)),
            ("Noise-Cancelling Headphones", "\U0001F3A7", ["anc", "over-ear", "bluetooth", "comfort", "audio"], (89, 399)),
            ("Laptop Stand", "\U0001F4BB", ["aluminum", "ergonomic", "adjustable", "desk", "cooling"], (22, 89)),
            ("Full HD Webcam", "\U0001F4F7", ["1080p", "auto-focus", "dual-mic", "streaming", "usb"], (25, 119)),
        ],
    },
    "Fashion": {
        "brands": ["Vellora", "Norwood & Co", "Traska", "Indigo Row", "Marlowe"],
        "types": [
            ("Leather Jacket", "\U0001F9F5", ["leather", "biker", "zip", "classic", "outerwear"], (89, 349)),
            ("Slim Denim Jeans", "\U0001F456", ["denim", "slim-fit", "stretch", "casual", "pants"], (39, 119)),
            ("Organic Cotton T-Shirt", "\U0001F455", ["cotton", "organic", "crew-neck", "basics", "unisex"], (14, 45)),
            ("Everyday Sneakers", "\U0001F45F", ["canvas", "cushioned", "lightweight", "casual", "shoes"], (45, 159)),
            ("Merino Wool Scarf", "\U0001F9E3", ["wool", "merino", "winter", "soft", "accessory"], (19, 69)),
            ("Polarized Sunglasses", "\U0001F576️", ["polarized", "uv400", "metal-frame", "summer", "accessory"], (25, 120)),
            ("Canvas Backpack", "\U0001F392", ["canvas", "laptop-compartment", "water-repellent", "travel", "bag"], (35, 129)),
            ("Denim Jacket", "\U0001F9F5", ["denim", "oversized", "vintage", "outerwear", "classic"], (55, 169)),
            ("Floral Summer Dress", "\U0001F457", ["floral", "rayon", "midi", "summer", "dress"], (32, 98)),
            ("Chronograph Watch", "⌚", ["stainless-steel", "quartz", "water-resistant", "classic", "accessory"], (69, 299)),
        ],
    },
    "Home & Kitchen": {
        "brands": ["Hearthstone", "Cucina", "NordicNest", "Lumen Home"],
        "types": [
            ("Ceramic Dinnerware Set", "\U0001F37D️", ["ceramic", "dishwasher-safe", "16-piece", "dining", "set"], (49, 169)),
            ("Cast Iron Skillet", "\U0001F373", ["cast-iron", "pre-seasoned", "oven-safe", "cooking", "durable"], (24, 89)),
            ("Digital Air Fryer", "\U0001F35F", ["air-fry", "digital", "5.8qt", "cooking", "healthy"], (69, 189)),
            ("Soy Wax Candle", "\U0001F56F️", ["soy-wax", "lavender", "40-hour", "aromatherapy", "gift"], (12, 38)),
            ("Memory Foam Pillow", "\U0001F6CF️", ["memory-foam", "orthopedic", "cooling-gel", "sleep", "bedroom"], (29, 89)),
            ("Robot Vacuum", "\U0001F916", ["robot", "self-charging", "app-control", "quiet", "cleaning"], (119, 449)),
            ("Espresso Machine", "☕", ["espresso", "15-bar", "milk-frother", "coffee", "stainless"], (99, 399)),
            ("Nonstick Frying Pan", "\U0001F373", ["nonstick", "granite-coating", "induction", "cooking", "pan"], (19, 65)),
            ("LED Table Lamp", "\U0001F4A1", ["led", "dimmable", "usb-charging", "desk", "lighting"], (18, 59)),
            ("Chunky Knit Throw Blanket", "\U0001F6CB️", ["knit", "cozy", "machine-wash", "sofa", "decor"], (25, 79)),
        ],
    },
    "Beauty": {
        "brands": ["Bloom & Glow", "Velvette", "Aether Botanics"],
        "types": [
            ("Vitamin C Face Serum", "\U0001F4A7", ["vitamin-c", "brightening", "hyaluronic", "skincare", "serum"], (15, 62)),
            ("Matte Liquid Lipstick", "\U0001F484", ["matte", "long-wear", "transfer-proof", "makeup", "lip"], (9, 32)),
            ("Argan Oil Shampoo", "\U0001F9F4", ["argan", "sulfate-free", "hydrating", "haircare", "shampoo"], (12, 38)),
            ("Daily Face Moisturizer", "\U0001F9F4", ["spf-30", "non-greasy", "vegan", "skincare", "lotion"], (14, 48)),
            ("Eau de Parfum", "\U0001F338", ["floral", "long-lasting", "unisex", "fragrance", "amber"], (35, 160)),
            ("Ionic Hair Dryer", "\U0001F4A8", ["ionic", "fast-dry", "diffuser", "haircare", "travel"], (29, 129)),
            ("Gel Nail Lacquer Set", "\U0001F485", ["gel", "6-colors", "glossy", "nails", "set"], (14, 44)),
            ("Mineral Sunscreen SPF 50", "☀️", ["spf-50", "mineral", "reef-safe", "skincare", "face"], (13, 42)),
        ],
    },
    "Sports & Outdoors": {
        "brands": ["Trailpeak", "Vitalize", "StormRidge"],
        "types": [
            ("Non-Slip Yoga Mat", "\U0001F9D8", ["yoga", "non-slip", "tpe", "fitness", "carry-strap"], (18, 74)),
            ("Resistance Bands Set", "\U0001F4AA", ["resistance", "5-levels", "home-workout", "fitness", "bands"], (12, 42)),
            ("40L Hiking Backpack", "\U0001F392", ["hiking", "rain-cover", "40l", "outdoor", "backpack"], (42, 139)),
            ("Insulated Water Bottle", "\U0001F964", ["insulated", "stainless", "24h-cold", "outdoor", "bottle"], (16, 55)),
            ("Trail Running Shoes", "\U0001F45F", ["trail", "grip", "breathable", "running", "shoes"], (59, 179)),
            ("2-Person Camping Tent", "⛺", ["2-person", "waterproof", "quick-setup", "camping", "tent"], (69, 249)),
            ("Speed Skipping Rope", "\U0001FA60", ["adjustable", "ball-bearing", "cardio", "fitness", "rope"], (8, 28)),
            ("Adjustable Dumbbell Set", "\U0001F3CB️", ["adjustable", "52lb", "strength", "home-gym", "weights"], (89, 329)),
            ("Cycling Helmet", "\U0001F6B2", ["ventilated", "adjustable", "led-tail", "cycling", "safety"], (28, 99)),
        ],
    },
    "Books": {
        "brands": ["Quill & Page"],
        "types": [
            ("Mystery Novel: The Silent Harbor", "\U0001F4D6", ["mystery", "thriller", "fiction", "bestseller", "paperback"], (9, 24)),
            ("Sci-Fi Epic: Signals from Vega", "\U0001F680", ["sci-fi", "space", "fiction", "hardcover", "adventure"], (11, 30)),
            ("Self-Help: Focus Formula", "\U0001F4D7", ["productivity", "self-help", "habits", "nonfiction", "mindset"], (10, 26)),
            ("The Weeknight Cookbook", "\U0001F4D5", ["cooking", "recipes", "30-minute", "food", "hardcover"], (14, 34)),
            ("Fantasy Trilogy: Ash & Crown", "\U0001F409", ["fantasy", "dragons", "boxed-set", "fiction", "epic"], (18, 49)),
            ("Biography: The Bridge Builder", "\U0001F4DC", ["biography", "history", "leadership", "nonfiction", "memoir"], (12, 28)),
            ("Poetry: Saltwater Lines", "\U0001F4DD", ["poetry", "nature", "contemporary", "verse", "gift"], (8, 20)),
            ("Business: Lean Momentum", "\U0001F4C8", ["business", "startups", "strategy", "nonfiction", "growth"], (13, 32)),
        ],
    },
}

COLOR_WORDS = ["Black", "Ivory", "Slate", "Sand", "Olive", "Charcoal", "Burgundy", "Sky", "Forest", "Blush", "Graphite", "Cream"]
VARIANTS = ["", "", " Pro", " Lite", " v2", " Max", " Plus", " Edition", " Air", " Classic"]
FEATURES = [
    "premium materials and reinforced stitching",
    "a refined finish that ages beautifully",
    "thoughtful details and a clean silhouette",
    "everyday durability without extra bulk",
    "an award-winning design language",
    "eco-conscious packaging and sourcing",
]
USECASES = [
    "daily use", "travel", "gifting", "the office", "weekend adventures",
    "small apartments", "busy mornings", "studio setups", "family dinners", "first apartments",
]


def main():
    products = []
    pid = 101
    for category, spec in CATALOG.items():
        for ptype, emoji, tags, (lo, hi) in spec["types"]:
            n = 2 if len(spec["types"]) >= 9 else 3
            used = set()
            for _ in range(n):
                brand = random.choice(spec["brands"])
                variant = random.choice(VARIANTS)
                color = random.choice(COLOR_WORDS)
                name = f"{brand} {color} {ptype}{variant}".strip()
                while name in used:
                    variant = random.choice(VARIANTS)
                    color = random.choice(COLOR_WORDS)
                    name = f"{brand} {color} {ptype}{variant}".strip()
                used.add(name)
                price = round(random.uniform(lo, hi), 2)
                rating = round(random.uniform(3.6, 4.9), 1)
                rating_count = int(random.triangular(40, 9500, 1200))
                stock = random.randint(0, 420)
                age_days = random.randint(1, 500)
                description = (
                    f"The {brand} {ptype} blends {random.choice(FEATURES)} with "
                    f"{random.choice(FEATURES).split(' and ')[-1]}. Designed for {random.choice(USECASES)}."
                )
                ptags = list(tags)
                if variant.strip():
                    ptags.append(variant.strip().lower())
                ptags.append(color.lower())
                products.append({
                    "id": pid,
                    "name": name,
                    "brand": brand,
                    "category": category,
                    "type": ptype,
                    "price": price,
                    "rating": rating,
                    "rating_count": rating_count,
                    "stock": stock,
                    "tags": ptags,
                    "description": description,
                    "emoji": emoji,
                    "age_days": age_days,
                })
                pid += 1
    # stability score used by "trending": popularity x rating x recency
    for p in products:
        pop = math.log1p(p["rating_count"])
        recency = 1.0 + 0.6 * (1.0 - min(p["age_days"], 500) / 500.0)
        p["trending_score"] = round((p["rating"] ** 1.6) * pop * recency, 4)

    out = Path(__file__).parent / "products.json"
    out.write_text(json.dumps(products, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(products)} products -> {out}")


if __name__ == "__main__":
    main()
