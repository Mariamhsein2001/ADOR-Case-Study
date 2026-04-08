# fields.py
# All field mappings, target entities, and the lookup table

from Levenshtein import distance as levenshtein_distance

# ---------------------------------------------------------------------------
# FIELD MAP
# Entity Name -> list of all possible label variants found in DOCX files
# ---------------------------------------------------------------------------
FIELD_MAP = {
    "Counterparty":           ["party a"],
    "Party B":                ["party b"],
    "Trade Date":             ["trade date"],
    "Trade Time":             ["trade time"],
    "Initial Valuation Date": ["initial valuation date"],
    "Effective Date":         ["effective date"],
    "Valuation Date":         ["valuation date"],
    "Maturity":               ["termination date"],
    "Termination Time":       ["termination time"],
    "Notional":               ["notional amount (n)", "notional amount"],
    "Upfront Payment":        ["upfront payment"],
    "Underlying":             ["underlying"],
    "Exchange":               ["exchange"],
    "Coupon":                 ["coupon (c)", "coupon"],
    "Barrier":                ["barrier (b)", "barrier"],
    "Interest Payments":      ["interest payments"],
    "Initial Price":          ["initial price (shareini)"],
    "Final Price":            ["sharefinal"],
    "Future Price Valuation": ["future price valuation"],
    "Calendar":               ["business day"],
    "Calculation Agent":      ["calculation agent"],
    "ISDA Documentation":     ["isda documentation"],
}

# ---------------------------------------------------------------------------
# TARGET ENTITIES — the 9 required by the case study
# ---------------------------------------------------------------------------
TARGET_ENTITIES = [
    "Counterparty",
    "Initial Valuation Date",
    "Notional",
    "Valuation Date",
    "Maturity",
    "Underlying",
    "Coupon",
    "Barrier",
    "Calendar",
]

# ---------------------------------------------------------------------------
# LABEL LOOKUP — auto-built reverse map: "variant" -> "EntityName"
# ---------------------------------------------------------------------------
LABEL_LOOKUP: dict[str, str] = {
    variant: entity
    for entity, variants in FIELD_MAP.items()
    for variant in variants
}

ALL_VARIANTS: list[str] = list(LABEL_LOOKUP.keys())


# ---------------------------------------------------------------------------
# FUZZY MATCH using Levenshtein distance
# ---------------------------------------------------------------------------
def fuzzy_match(key: str, max_distance: int = 2):
    """
    Try exact match first.
    If no exact match, find closest variant within max_distance edits.
    Returns: (entity_name, matched_variant, is_fuzzy, distance)
    """
    if key in LABEL_LOOKUP:
        return LABEL_LOOKUP[key], key, False, 0

    best_variant  = None
    best_distance = float("inf")

    for variant in ALL_VARIANTS:
        dist = levenshtein_distance(key, variant)
        if dist < best_distance:
            best_distance = dist
            best_variant  = variant

    if best_distance <= max_distance:
        return LABEL_LOOKUP[best_variant], best_variant, True, best_distance

    return None, None, False, None
