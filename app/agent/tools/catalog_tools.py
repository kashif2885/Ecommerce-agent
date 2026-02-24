"""
Product catalog tools – backed by a hardcoded mock catalog of 10
generic e-commerce products across diverse categories.

Tool descriptions are intentionally detailed so the ReAct LLM can
route product-related queries correctly without an external classifier.
"""
from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Mock product catalog
# ---------------------------------------------------------------------------

PRODUCT_CATALOG: list[dict] = [
    {
        "id": "PROD001",
        "name": "UltraBook Pro 15",
        "category": "Laptops",
        "brand": "TechMaster",
        "price": 1299.99,
        "description": "High-performance 15.6\" laptop with 4K OLED display, Intel i9, 32 GB RAM, 1 TB SSD.",
        "specs": {
            "processor": "Intel Core i9-13900H",
            "ram": "32 GB DDR5",
            "storage": "1 TB NVMe SSD",
            "display": "15.6\" 4K OLED",
            "battery": "86 Wh – 12 hr",
            "weight": "1.8 kg",
        },
        "rating": 4.8,
        "stock": 45,
        "tags": ["laptop", "ultrabook", "high-performance", "professional"],
    },
    {
        "id": "PROD002",
        "name": "SmartHome Hub X200",
        "category": "Smart Home",
        "brand": "ConnectIQ",
        "price": 149.99,
        "description": "Central smart-home hub supporting 200+ integrations via Wi-Fi 6, Zigbee, Z-Wave, and Bluetooth 5.",
        "specs": {
            "connectivity": "Wi-Fi 6, Zigbee, Z-Wave, Bluetooth 5.0",
            "compatibility": "200+ smart-home brands",
            "voice_assistants": "Alexa, Google, Siri",
            "local_processing": "Yes",
            "max_devices": 100,
        },
        "rating": 4.6,
        "stock": 120,
        "tags": ["smart home", "hub", "automation", "connectivity"],
    },
    {
        "id": "PROD003",
        "name": "ProSound ANC Headphones",
        "category": "Audio",
        "brand": "AudioPeak",
        "price": 349.99,
        "description": "Premium wireless headphones with industry-leading ANC (-35 dB) and 40-hour battery.",
        "specs": {
            "drivers": "40 mm custom dynamic",
            "frequency_response": "20 Hz – 20 kHz",
            "anc": "Hybrid ANC -35 dB",
            "battery": "40 hr ANC on",
            "charging": "USB-C; 10 min → 3 hr",
            "codecs": "LDAC, aptX HD, AAC, SBC",
        },
        "rating": 4.9,
        "stock": 78,
        "tags": ["headphones", "wireless", "ANC", "audio", "premium"],
    },
    {
        "id": "PROD004",
        "name": "UltraBook Air 13",
        "category": "Laptops",
        "brand": "TechMaster",
        "price": 899.99,
        "description": "Ultra-thin 13\" travel laptop, AMD Ryzen 7, 16 GB RAM, 18-hour battery life.",
        "specs": {
            "processor": "AMD Ryzen 7 7840U",
            "ram": "16 GB LPDDR5",
            "storage": "512 GB NVMe SSD",
            "display": "13.3\" 2K IPS",
            "battery": "65 Wh – 18 hr",
            "weight": "1.1 kg",
        },
        "rating": 4.7,
        "stock": 92,
        "tags": ["laptop", "ultrabook", "lightweight", "travel"],
    },
    {
        "id": "PROD005",
        "name": "GameZone Controller Pro",
        "category": "Gaming",
        "brand": "GameZone",
        "price": 79.99,
        "description": "Professional wireless gaming controller with adaptive triggers and haptic feedback.",
        "specs": {
            "compatibility": "PC, PS5, Xbox, Mobile",
            "connectivity": "2.4 GHz wireless, Bluetooth, USB-C",
            "battery": "40 hr",
            "haptic": "HD rumble",
            "triggers": "Adaptive",
        },
        "rating": 4.7,
        "stock": 200,
        "tags": ["gaming", "controller", "wireless", "haptic"],
    },
    {
        "id": "PROD006",
        "name": "4K Action Camera Xtreme",
        "category": "Cameras",
        "brand": "ActionViz",
        "price": 399.99,
        "description": "Rugged 4K action camera with 3-axis stabilisation, waterproof to 30 m.",
        "specs": {
            "video": "4K 120 fps / 1080p 240 fps",
            "photo": "20 MP",
            "stabilisation": "3-axis HyperSmooth 6.0",
            "waterproof": "30 m without case",
            "battery": "2.5 hr @ 4K30",
            "screen": "2.27\" touch",
        },
        "rating": 4.8,
        "stock": 56,
        "tags": ["camera", "action", "waterproof", "4K", "sports"],
    },
    {
        "id": "PROD007",
        "name": "ErgoDesk Electric Standing Desk",
        "category": "Office",
        "brand": "ErgoLife",
        "price": 649.99,
        "description": "Electric height-adjustable standing desk with 3 memory presets and anti-collision.",
        "specs": {
            "height_range": "60 – 125 cm",
            "load_capacity": "100 kg",
            "surface": "140 × 70 cm",
            "motor": "Dual, whisper-quiet",
            "memory_presets": 3,
            "warranty": "5 years",
        },
        "rating": 4.6,
        "stock": 34,
        "tags": ["desk", "standing desk", "ergonomic", "office"],
    },
    {
        "id": "PROD008",
        "name": "SmartWatch Ultra SE",
        "category": "Wearables",
        "brand": "WristTech",
        "price": 499.99,
        "description": "Premium smartwatch with ECG, blood-glucose monitoring, multi-band GPS, and 5-day battery.",
        "specs": {
            "display": "1.9\" AMOLED LTPO",
            "sensors": "ECG, SpO2, Glucose, Temp",
            "gps": "Multi-band",
            "battery": "5 days typical",
            "water_resistance": "100 m",
            "compatibility": "iOS & Android",
        },
        "rating": 4.7,
        "stock": 89,
        "tags": ["smartwatch", "wearable", "health", "fitness"],
    },
    {
        "id": "PROD009",
        "name": "Portable SSD TurboX 2 TB",
        "category": "Storage",
        "brand": "DataSwift",
        "price": 189.99,
        "description": "Rugged 2 TB portable SSD, USB 3.2 Gen 2×2 (20 Gbps), IP55 rated.",
        "specs": {
            "capacity": "2 TB",
            "interface": "USB 3.2 Gen 2×2 – 20 Gbps",
            "read_speed": "2000 MB/s",
            "write_speed": "1800 MB/s",
            "durability": "IP55, 3 m drop-proof",
            "weight": "42 g",
        },
        "rating": 4.8,
        "stock": 145,
        "tags": ["storage", "SSD", "portable", "backup"],
    },
    {
        "id": "PROD010",
        "name": "RGB Mechanical Keyboard TKL",
        "category": "Peripherals",
        "brand": "KeyCraft",
        "price": 149.99,
        "description": "Tenkeyless hot-swap mechanical keyboard with per-key RGB and wireless connectivity.",
        "specs": {
            "form_factor": "TKL – 87 keys",
            "switches": "Hot-swappable 5-pin",
            "connectivity": "2.4 GHz, Bluetooth 5.0, USB-C",
            "battery": "4000 mAh – ~3 months no-RGB",
            "backlight": "Per-key RGB",
            "anti_ghosting": "NKRO",
        },
        "rating": 4.7,
        "stock": 112,
        "tags": ["keyboard", "mechanical", "RGB", "gaming", "wireless"],
    },
]

_PRODUCT_BY_ID = {p["id"]: p for p in PRODUCT_CATALOG}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def search_products(query: str, category: str = "") -> list:
    """Search the product catalog by keyword and return the most relevant matches.

    Use this tool when the user:
      - Asks what products are available (e.g. 'do you have headphones?')
      - Wants a recommendation (e.g. 'best laptop under $1000')
      - Is looking for products in a specific category
      - Asks a vague product question that requires a search first

    The search scores each product by how many query words appear in its
    name, description, category, brand, and tags, then returns the top 5
    results sorted by relevance and rating.

    After calling this tool, offer to show full details or compare items
    using get_product_details or compare_products.

    Args:
        query: Free-text search terms (e.g. 'wireless noise cancelling headphones',
               'gaming controller', 'lightweight laptop for travel').
        category: Optional exact category name to filter results.
                  Available categories: Laptops, Audio, Gaming, Cameras,
                  Smart Home, Office, Wearables, Storage, Peripherals.
                  Leave blank to search all categories.

    Returns:
        A list of up to 5 product dicts, each containing: id, name,
        category, brand, price, rating, description, and relevance_score.
        Returns an empty list if nothing matches.
    """
    query_lower = query.lower()
    results: list[dict] = []

    for product in PRODUCT_CATALOG:
        if category and product["category"].lower() != category.lower():
            continue

        search_text = " ".join(
            [
                product["name"],
                product["description"],
                product["category"],
                product["brand"],
                " ".join(product["tags"]),
            ]
        ).lower()

        score = sum(1 for word in query_lower.split() if word in search_text)
        if score > 0:
            results.append(
                {
                    "id": product["id"],
                    "name": product["name"],
                    "category": product["category"],
                    "brand": product["brand"],
                    "price": product["price"],
                    "rating": product["rating"],
                    "description": product["description"],
                    "relevance_score": score,
                }
            )

    results.sort(key=lambda x: (-x["relevance_score"], -x["rating"]))
    return results[:5]


@tool
def get_product_details(product_id: str) -> dict:
    """Retrieve complete details for a specific product by its ID.

    Use this tool when the user:
      - Asks for more information about a product they've seen in search results
      - Wants to know the full specifications of a specific item
      - Asks about stock availability or exact pricing of one product
      - References a product by its ID (e.g. 'tell me more about PROD003')

    Product IDs are returned by search_products and follow the format
    PROD001 through PROD010.

    Args:
        product_id: The product identifier string (case-insensitive),
                    e.g. 'PROD001' or 'prod003'.

    Returns:
        The full product dict including: id, name, category, brand, price,
        description, specs (detailed key-value pairs), rating, stock count,
        and tags.  Returns an error dict with all available IDs if the
        product is not found.
    """
    product = _PRODUCT_BY_ID.get(product_id.upper())
    if not product:
        return {
            "error": f"Product '{product_id}' not found.",
            "available_ids": list(_PRODUCT_BY_ID.keys()),
        }
    return product


@tool
def compare_products(product_ids: list) -> dict:
    """Compare two or more products side-by-side on price, rating, and specs.

    Use this tool when the user:
      - Wants to compare specific products (e.g. 'compare PROD001 and PROD004')
      - Asks 'which is better between X and Y?'
      - Has narrowed down to a shortlist and wants a direct comparison
      - Asks to compare items by name after a search

    Provide at least two product IDs for a meaningful comparison.
    You can find product IDs using the search_products tool first if needed.

    Args:
        product_ids: A list of product ID strings to compare
                     (e.g. ['PROD001', 'PROD004'] or ['PROD003', 'PROD008']).
                     Accepts 2 or more IDs.  IDs are case-insensitive.

    Returns:
        A comparison dict containing:
          - 'products': summary list (id, name, category, brand, price, rating)
          - 'spec_comparison': dict of spec keys → {product_name: value}
            for easy side-by-side reading
          - 'not_found': list of any IDs that could not be located
    """
    found: list[dict] = []
    not_found: list[str] = []

    for pid in product_ids:
        product = _PRODUCT_BY_ID.get(pid.upper())
        if product:
            found.append(product)
        else:
            not_found.append(pid)

    if not found:
        return {"error": "No valid products found.", "not_found": not_found}

    all_spec_keys: set[str] = set()
    for p in found:
        all_spec_keys.update(p.get("specs", {}).keys())

    side_by_side: dict[str, dict] = {}
    for key in sorted(all_spec_keys):
        side_by_side[key] = {p["name"]: p.get("specs", {}).get(key, "N/A") for p in found}

    comparison: dict = {
        "products": [
            {
                "id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "brand": p["brand"],
                "price": p["price"],
                "rating": p["rating"],
            }
            for p in found
        ],
        "spec_comparison": side_by_side,
    }

    if not_found:
        comparison["not_found"] = not_found

    return comparison
