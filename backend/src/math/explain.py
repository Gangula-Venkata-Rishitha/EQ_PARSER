"""Equation to NLP explanation conversion."""

from typing import Dict, Optional
from ..glossary.glossary import Glossary
from .lexer import tokenize_equation, OPERATOR, EQUALS, SYMBOL, NUMBER
import re


# Common symbol to meaning mappings (used if not in glossary)
SYMBOL_MEANINGS: Dict[str, str] = {
    "F": "force", "f": "force",
    "ΣF": "net force", "sum_F": "net force",
    "F_net": "net force",
    "m": "mass",
    "a": "acceleration",
    "g": "gravity",
    "v": "velocity",
    "u": "initial velocity", "u0": "initial velocity",
    "t": "time",
    "s": "distance", "d": "distance",
    "K": "kinetic energy", "Ek": "kinetic energy",
    "U": "potential energy", "Ep": "potential energy",
    "E": "energy",
    "W": "work",
    "p": "momentum",
    "P": "power",
    "T": "temperature",
    "c": "speed of light",
    "h": "Planck constant",
}


def equation_to_nlp(equation: str, glossary: Optional[Glossary] = None) -> str:
    """Convert equation to natural language explanation.
    
    Args:
        equation: Equation string (normalized)
        glossary: Glossary for symbol meanings (optional)
        
    Returns:
        Natural language explanation
    """
    # Tokenize equation
    tokens = tokenize_equation(equation)
    
    if not tokens:
        return equation
    
    # Split into LHS and RHS
    equals_idx = None
    for i, token in enumerate(tokens):
        if token.type == EQUALS:
            equals_idx = i
            break
    
    if equals_idx is None:
        # No equals sign - just describe expression
        return _explain_expression(tokens, glossary)
    
    lhs_tokens = tokens[:equals_idx]
    rhs_tokens = tokens[equals_idx + 1:]
    
    lhs_text = _explain_expression(lhs_tokens, glossary)
    rhs_text = _explain_expression(rhs_tokens, glossary)
    
    return f"{lhs_text} equals {rhs_text}."


def _explain_expression(tokens, glossary: Optional[Glossary] = None) -> str:
    """Explain a mathematical expression.
    
    Args:
        tokens: List of tokens
        glossary: Glossary for symbol meanings
        
    Returns:
        Natural language description
    """
    if not tokens:
        return ""
    
    # Convert tokens to readable form
    parts = []
    i = 0
    
    while i < len(tokens):
        token = tokens[i]
        
        if token.type == SYMBOL:
            # Look up meaning
            meaning = _get_symbol_meaning(token.value, glossary)
            parts.append(meaning)
        elif token.type == NUMBER:
            parts.append(token.value)
        elif token.type == OPERATOR:
            if token.value == "+":
                if i == 0 or i == len(tokens) - 1:
                    parts.append("plus")
                else:
                    parts.append("plus")
            elif token.value == "-":
                if i == 0:
                    parts.append("minus")
                else:
                    parts.append("minus")
            elif token.value == "*":
                if i < len(tokens) - 1:
                    # Check if this is product context
                    parts.append("times")
                else:
                    parts.append("multiplied by")
            elif token.value == "/":
                parts.append("divided by")
            elif token.value == "^" or token.value == "**":
                if i > 0:
                    parts.append("to the power of")
        elif token.value == "(":
            parts.append("(")
        elif token.value == ")":
            parts.append(")")
        
        i += 1
    
    # Join parts with natural language
    explanation = " ".join(parts)
    
    # Post-process for natural flow
    # "times" -> "the product of"
    explanation = re.sub(r'(\w+)\s+times\s+(\w+)', r'the product of \1 and \2', explanation, count=1)
    
    # "divided by" -> "divided by"
    explanation = re.sub(r'(\w+)\s+divided by\s+(\w+)', r'\1 divided by \2', explanation)
    
    # "plus" -> "the sum of"
    explanation = re.sub(r'(\w+)\s+plus\s+(\w+)', r'the sum of \1 and \2', explanation, count=1)
    
    # Clean up
    explanation = explanation.replace("  ", " ")
    explanation = explanation.strip()
    
    return explanation


def _get_symbol_meaning(symbol: str, glossary: Optional[Glossary] = None) -> str:
    """Get symbol meaning from glossary or defaults.
    
    Args:
        symbol: Symbol name
        glossary: Glossary (optional)
        
    Returns:
        Symbol meaning/description
    """
    # Try glossary first
    if glossary:
        sym = glossary.get_symbol(symbol)
        if sym and sym.meaning:
            return sym.meaning
    
    # Fall back to default meanings
    if symbol in SYMBOL_MEANINGS:
        return SYMBOL_MEANINGS[symbol]
    
    # Return symbol as-is
    return symbol
