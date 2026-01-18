"""Equation normalization: unicode to ASCII, symbol normalization."""

from typing import Dict
import re


# Unicode to ASCII mappings for math symbols
UNICODE_TO_ASCII: Dict[str, str] = {
    # Greek letters (common)
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon",
    "θ": "theta", "λ": "lambda", "μ": "mu", "π": "pi", "ρ": "rho",
    "σ": "sigma", "τ": "tau", "φ": "phi", "χ": "chi", "ω": "omega",
    "Α": "Alpha", "Β": "Beta", "Γ": "Gamma", "Δ": "Delta", "Θ": "Theta",
    "Λ": "Lambda", "Π": "Pi", "Σ": "Sigma", "Φ": "Phi", "Ω": "Omega",
    
    # Math operators
    "∑": "sum", "Σ": "Sigma",  # Summation
    "∫": "integral",  # Integral
    "∂": "partial",  # Partial derivative
    "∇": "nabla",  # Nabla
    "√": "sqrt",  # Square root
    "±": "+-",  # Plus-minus
    "×": "*",  # Multiplication
    "÷": "/",  # Division
    "≤": "<=",  # Less or equal
    "≥": ">=",  # Greater or equal
    "≠": "!=",  # Not equal
    "≈": "~=",  # Approximately
    "∞": "inf",  # Infinity
    "∏": "product",  # Product
    
    # Subscripts/superscripts (handled separately)
    "²": "^2", "³": "^3", "¹": "^1",
}


def normalize_equation(equation: str) -> str:
    """Normalize equation string (unicode to ASCII, symbol normalization).
    
    Args:
        equation: Raw equation string
        
    Returns:
        Normalized equation string
    """
    # Replace unicode symbols
    normalized = equation
    for unicode_char, ascii_replacement in UNICODE_TO_ASCII.items():
        normalized = normalized.replace(unicode_char, ascii_replacement)
    
    # Normalize summation: Σ/∑ -> sum()
    normalized = re.sub(r'([∑Σ])\s*', r'sum_', normalized)
    
    # Normalize exponents: x² -> x^2, x³ -> x^3
    normalized = re.sub(r'(\w+)([²³¹])', lambda m: f"{m.group(1)}^{_superscript_to_num(m.group(2))}", normalized)
    
    # Normalize implicit multiplication (e.g., "2x" -> "2*x", but careful with units)
    # This is tricky - skip for now to avoid false positives
    
    # Normalize spaces around operators
    normalized = re.sub(r'\s*([+\-*/=^])\s*', r' \1 ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.strip()
    
    return normalized


def _superscript_to_num(superscript: str) -> str:
    """Convert superscript to number.
    
    Args:
        superscript: Superscript character
        
    Returns:
        Number string
    """
    superscript_map = {"¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5",
                       "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁰": "0"}
    return superscript_map.get(superscript, superscript)


def normalize_summation_symbol(equation: str) -> str:
    """Normalize summation symbols (Σ/∑ -> sum notation).
    
    Args:
        equation: Equation string
        
    Returns:
        Equation with normalized summation
    """
    # Replace Σ and ∑ with "sum" prefix
    normalized = re.sub(r'[∑Σ]', 'sum', equation)
    return normalized
