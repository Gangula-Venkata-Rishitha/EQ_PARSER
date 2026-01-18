"""Unit normalization and inference."""

from typing import Optional, Dict, Pattern
import re


# Unit normalization mappings
UNIT_NORMALIZATIONS: Dict[str, str] = {
    # Length
    "m": "m", "meter": "m", "meters": "m",
    "cm": "cm", "centimeter": "cm", "centimeters": "cm",
    "mm": "mm", "millimeter": "mm", "millimeters": "mm",
    "km": "km", "kilometer": "km", "kilometers": "km",
    "in": "in", "inch": "in", "inches": "in",
    "ft": "ft", "foot": "ft", "feet": "ft",
    
    # Time
    "s": "s", "sec": "s", "second": "s", "seconds": "s",
    "min": "min", "minute": "min", "minutes": "min",
    "h": "h", "hr": "h", "hour": "h", "hours": "h",
    
    # Mass
    "kg": "kg", "kilogram": "kg", "kilograms": "kg",
    "g": "g", "gram": "g", "grams": "g",
    "lb": "lb", "pound": "lb", "pounds": "lb",
    
    # Force
    "N": "N", "newton": "N", "newtons": "N",
    
    # Energy
    "J": "J", "joule": "J", "joules": "J",
    
    # Velocity
    "m/s": "m/s", "m s^-1": "m/s",
    "km/h": "km/h", "kmh": "km/h",
    
    # Acceleration
    "m/s^2": "m/s²", "m s^-2": "m/s²", "m/s2": "m/s²",
    
    # Frequency
    "Hz": "Hz", "hertz": "Hz",
}


def normalize_unit(unit: str) -> str:
    """Normalize unit string.
    
    Args:
        unit: Unit string to normalize
        
    Returns:
        Normalized unit string
    """
    if not unit:
        return ""
    
    unit_clean = unit.strip().lower()
    
    # Check direct mapping
    if unit_clean in UNIT_NORMALIZATIONS:
        return UNIT_NORMALIZATIONS[unit_clean]
    
    # Try pattern matching for compound units
    # Pattern: "m/s^2", "m s^-2", etc.
    compound_patterns = [
        (r'^([a-z]+)\s*/\s*([a-z]+)\s*\^\s*(\d+)$', lambda m: f"{m.group(1)}/{m.group(2)}{_to_superscript(m.group(3))}"),
        (r'^([a-z]+)\s*/\s*([a-z]+)$', lambda m: f"{m.group(1)}/{m.group(2)}"),
        (r'^([a-z]+)\s*\^\s*(\d+)$', lambda m: f"{m.group(1)}{_to_superscript(m.group(2))}"),
    ]
    
    for pattern, replacement in compound_patterns:
        match = re.match(pattern, unit_clean)
        if match:
            return replacement(match)
    
    # Return original if no match
    return unit


def _to_superscript(num_str: str) -> str:
    """Convert number to superscript.
    
    Args:
        num_str: Number string
        
    Returns:
        Superscript string
    """
    superscript_map = {"0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
                       "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"}
    return "".join(superscript_map.get(c, c) for c in num_str)


def infer_unit_from_symbol(symbol: str) -> Optional[str]:
    """Infer unit from symbol name (heuristic).
    
    Args:
        symbol: Symbol name
        
    Returns:
        Inferred unit if found, None otherwise
    """
    symbol_lower = symbol.lower()
    
    # Common symbol -> unit mappings
    mappings = {
        "mass": "kg",
        "m": "kg",  # Common for mass
        "weight": "N",
        "force": "N",
        "f": "N",
        "velocity": "m/s",
        "v": "m/s",
        "speed": "m/s",
        "acceleration": "m/s²",
        "a": "m/s²",
        "time": "s",
        "t": "s",
        "distance": "m",
        "d": "m",
        "s": "m",
        "energy": "J",
        "e": "J",
        "power": "W",
        "p": "W",
    }
    
    # Direct match
    if symbol_lower in mappings:
        return mappings[symbol_lower]
    
    # Prefix match
    for key, unit in mappings.items():
        if symbol_lower.startswith(key) or key in symbol_lower:
            return unit
    
    return None
