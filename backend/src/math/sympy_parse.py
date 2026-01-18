"""Safe SymPy parsing (only if validator passes)."""

from typing import Optional, Tuple
import sympy
from sympy import sympify, SympifyError


def safe_parse_equation(equation: str) -> Tuple[Optional[sympy.Basic], Optional[str]]:
    """Safely parse equation using SymPy (only for validated equations).
    
    Args:
        equation: Equation string (should be validated first)
        
    Returns:
        Tuple of (sympy expression, error_message)
        Returns (None, error_message) if parsing fails
    """
    try:
        # Split into LHS and RHS if contains "="
        if "=" in equation:
            parts = equation.split("=", 1)
            lhs_str = parts[0].strip()
            rhs_str = parts[1].strip()
            
            # Parse both sides
            lhs = sympify(lhs_str, evaluate=False)
            rhs = sympify(rhs_str, evaluate=False)
            
            # Return as equation (Equality object)
            expr = sympy.Eq(lhs, rhs)
            return expr, None
        else:
            # Single expression
            expr = sympify(equation, evaluate=False)
            return expr, None
    
    except SympifyError as e:
        return None, f"SymPy parsing error: {str(e)}"
    except Exception as e:
        return None, f"Unexpected error during parsing: {str(e)}"


def extract_symbols_from_sympy(expr: sympy.Basic) -> list:
    """Extract symbol names from SymPy expression.
    
    Args:
        expr: SymPy expression
        
    Returns:
        List of symbol names (strings)
    """
    try:
        free_symbols = expr.free_symbols
        return sorted([str(symbol) for symbol in free_symbols])
    except Exception:
        return []
