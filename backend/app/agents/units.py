"""Unit parsing and conversion for the lab co-pilot's deterministic tools.

Every quantity is converted to one base unit per dimension before any comparison or
calculation, so "500 mL" and "0.5 L" are the same number. Units outside the tables
below (e.g. "bottle", "aliquot") are *counts*: they are never converted, and a
comparison between a count and a mass or volume is reported as not comparable.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

# dimension -> {normalised unit: factor to the base unit}
_UNITS: dict[str, dict[str, float]] = {
    "mass": {"kg": 1e3, "g": 1.0, "mg": 1e-3, "ug": 1e-6, "ng": 1e-9},  # base: g
    "volume": {"l": 1.0, "ml": 1e-3, "ul": 1e-6},  # base: L
    "molar": {"m": 1.0, "mm": 1e-3, "um": 1e-6, "nm": 1e-9},  # base: mol/L
    "mass_conc": {"g/l": 1.0, "mg/ml": 1.0, "mg/l": 1e-3, "ug/ml": 1e-3, "ug/l": 1e-6, "%w/v": 10.0},  # base: g/L
}
BASE_UNIT = {"mass": "g", "volume": "L", "molar": "M", "mass_conc": "g/L"}

_ALIASES = {
    "gram": "g", "grams": "g", "milligram": "mg", "milligrams": "mg", "microgram": "ug", "micrograms": "ug",
    "kilogram": "kg", "kilograms": "kg",
    "liter": "l", "litre": "l", "liters": "l", "litres": "l", "milliliter": "ml", "millilitre": "ml",
    "milliliters": "ml", "millilitres": "ml", "microliter": "ul", "microlitre": "ul", "microliters": "ul",
    "microlitres": "ul", "cc": "ml",
    "molar": "m", "mol/l": "m", "mmol/l": "mm", "umol/l": "um", "nmol/l": "nm", "millimolar": "mm",
    "micromolar": "um", "nanomolar": "nm",
    "%": "%w/v", "%(w/v)": "%w/v", "w/v%": "%w/v", "%wv": "%w/v",
}


class UnitError(ValueError):
    pass


def normalise_unit(unit: str) -> str:
    """Canonical spelling: lower case, no spaces, micro sign as 'u' ("µL" -> "ul", "1 M" unit "M" -> "m")."""
    u = (unit or "").strip().replace("µ", "u").replace("μ", "u").replace("ℓ", "l")
    u = re.sub(r"\s+", "", u).lower()
    return _ALIASES.get(u, u)


def dimension_of(unit: str) -> str | None:
    u = normalise_unit(unit)
    for dim, table in _UNITS.items():
        if u in table:
            return dim
    return None


def to_base(value: float, unit: str) -> tuple[str, float]:
    """``(dimension, value in the base unit)``; raises :class:`UnitError` for unknown units."""
    u = normalise_unit(unit)
    for dim, table in _UNITS.items():
        if u in table:
            return dim, float(value) * table[u]
    raise UnitError(f"Unknown or non-convertible unit '{unit}'.")


def convert(value: float, from_unit: str, to_unit: str) -> float:
    d1, base = to_base(value, from_unit)
    d2 = dimension_of(to_unit)
    if d1 != d2:
        raise UnitError(f"Cannot convert {from_unit} to {to_unit}.")
    return base / _UNITS[d2][normalise_unit(to_unit)]


def fmt_number(x: float, sig: int = 4) -> str:
    """Round to ``sig`` significant figures and drop trailing zeros (12.1140 -> "12.11", 500.0 -> "500")."""
    if x == 0 or not math.isfinite(x):
        return "0" if x == 0 else str(x)
    digits = sig - int(math.floor(math.log10(abs(x)))) - 1
    rounded = round(x, max(digits, 0))
    text = f"{rounded:.{max(digits, 0)}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


@dataclass(frozen=True)
class Quantity:
    value: float
    unit: str  # display unit

    def __str__(self) -> str:
        return f"{fmt_number(self.value)} {self.unit}"


_MASS_DISPLAY = [("kg", 1e3), ("g", 1.0), ("mg", 1e-3), ("µg", 1e-6)]
_VOLUME_DISPLAY = [("L", 1.0), ("mL", 1e-3), ("µL", 1e-6)]


def humanise(base_value: float, dimension: str) -> Quantity:
    """Pick a readable unit for a base-unit value (0.0121 g -> 12.1 mg)."""
    table = {"mass": _MASS_DISPLAY, "volume": _VOLUME_DISPLAY}.get(dimension)
    if table is None:
        return Quantity(base_value, BASE_UNIT.get(dimension, ""))
    for unit, factor in table:
        if abs(base_value) >= factor:
            return Quantity(base_value / factor, unit)
    unit, factor = table[-1]
    return Quantity(base_value / factor, unit)
