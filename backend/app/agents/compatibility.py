"""Chemical compatibility matrix used by ``tool_verify_chemical_compatibility``.

!!! LIMITED DEMO MATRIX - NOT EXPERT-REVIEWED !!!

This table is a small hand-written sample for demonstrating the co-pilot. It has not
been reviewed by a chemical safety professional and is NOT a substitute for the Safety
Data Sheets, your chemical hygiene plan or your EHS team. Any pair that is not listed
is reported as "unknown", which must never be read as "safe".

Keys are ``compounds.compound_key`` values. Lookups are symmetric.
"""
from __future__ import annotations

MATRIX_LABEL = "Limited demo matrix, not expert-reviewed."
MATRIX_REVIEWED = False

INCOMPATIBLE = "incompatible"
NO_KNOWN_ISSUE = "no_known_issue"
UNKNOWN = "unknown"

_PAIRS: dict[frozenset[str], tuple[str, str]] = {}


def _add(a: str, b: str, result: str, note: str) -> None:
    _PAIRS[frozenset((a, b))] = (result, note)


# --- Incompatible pairs (demo) ---------------------------------------------------
_add("sodium_hypochlorite", "hydrochloric_acid", INCOMPATIBLE,
     "Hypochlorite and acids release chlorine gas.")
_add("sodium_hypochlorite", "ammonium_hydroxide", INCOMPATIBLE,
     "Hypochlorite and ammonia form toxic chloramine gases.")
_add("sodium_hypochlorite", "ethanol", INCOMPATIBLE,
     "Hypochlorite and ethanol can form chloroform and other chlorinated by-products.")
_add("sodium_hypochlorite", "methanol", INCOMPATIBLE,
     "Hypochlorite and methanol can form chlorinated by-products.")
_add("sodium_hypochlorite", "acetone", INCOMPATIBLE,
     "Hypochlorite and acetone react to form chloroform.")
_add("sodium_hypochlorite", "hydrogen_peroxide", INCOMPATIBLE,
     "Hypochlorite and peroxide react vigorously with rapid oxygen release.")
_add("hydrogen_peroxide", "acetone", INCOMPATIBLE,
     "Peroxide and acetone can form explosive organic peroxides.")

# --- Pairs with no known issue in this demo matrix ---------------------------------
# "No known issue" only means this small table records no hazard for the pair.
for _a, _b in [
    ("tris_base", "sodium_chloride"), ("tris_base", "edta_disodium_dihydrate"),
    ("tris_hcl", "sodium_chloride"), ("tris_hcl", "edta_disodium_dihydrate"),
    ("sodium_chloride", "edta_disodium_dihydrate"), ("sodium_chloride", "potassium_chloride"),
    ("magnesium_chloride_hexahydrate", "tris_base"), ("magnesium_chloride_hexahydrate", "tris_hcl"),
    ("magnesium_chloride_hexahydrate", "sodium_chloride"), ("magnesium_chloride_hexahydrate", "potassium_chloride"),
    ("potassium_chloride", "tris_base"), ("potassium_chloride", "tris_hcl"),
    ("glycine", "tris_base"), ("sds", "tris_base"), ("sds", "glycine"), ("sds", "sodium_chloride"),
    ("acetonitrile", "methanol"),
]:
    _add(_a, _b, NO_KNOWN_ISSUE, "No hazard recorded for this pair in the limited demo matrix.")
_add("tris_base", "hydrochloric_acid", NO_KNOWN_ISSUE,
     "Used together for pH adjustment; add acid slowly, the reaction is exothermic.")


def lookup(a: str | None, b: str | None) -> tuple[str, str]:
    """``(result, note)`` for a pair of compound keys. Unlisted or unresolved pairs are ``unknown``."""
    if not a or not b:
        return UNKNOWN, "At least one reagent could not be identified, so the pair cannot be checked."
    if a == b:
        return NO_KNOWN_ISSUE, "Same compound."
    found = _PAIRS.get(frozenset((a, b)))
    if found is None:
        return UNKNOWN, "Pair not in the limited demo matrix. Unknown does not mean safe; check both SDSs."
    return found
