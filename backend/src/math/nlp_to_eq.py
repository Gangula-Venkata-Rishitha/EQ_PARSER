"""NLP to equation conversion (retrieval/synthesis)."""

from typing import List, Dict, Optional, Tuple
from ..glossary.glossary import Glossary
import re


# Known equation templates
EQUATION_TEMPLATES = {
    "newton_second": {
        "pattern": ["force", "mass", "acceleration"],
        "equation": "F = m * a",
        "alternatives": ["ΣF = m * a", "F_net = m * a"]
    },
    "weight": {
        "pattern": ["weight", "mass", "gravity"],
        "equation": "W = m * g",
        "alternatives": ["F = m * g"]
    },
    "kinetic_energy": {
        "pattern": ["kinetic", "energy", "mass", "velocity"],
        "equation": "K = (1/2) * m * v^2",
        "alternatives": ["Ek = (1/2) * m * v^2"]
    },
    "momentum": {
        "pattern": ["momentum", "mass", "velocity"],
        "equation": "p = m * v"
    },
    "velocity": {
        "pattern": ["velocity", "acceleration", "time"],
        "equation": "v = a * t",
        "alternatives": ["v = u + a * t"]
    },
}


# NLP phrase to symbol mapping
PHRASE_TO_SYMBOL: Dict[str, str] = {
    "force": "F", "net force": "ΣF", "net_force": "ΣF",
    "mass": "m",
    "acceleration": "a",
    "velocity": "v", "speed": "v",
    "time": "t",
    "distance": "s", "displacement": "s",
    "gravity": "g", "gravitational": "g",
    "kinetic energy": "K", "kinetic": "K",
    "potential energy": "U", "potential": "U",
    "energy": "E",
    "work": "W",
    "momentum": "p",
    "power": "P",
}


# Operator phrases
OPERATOR_PHRASES = {
    "product": "*", "multiply": "*", "multiplied": "*", "times": "*",
    "sum": "+", "add": "+", "added": "+", "plus": "+",
    "divide": "/", "divided": "/", "divided by": "/",
    "subtract": "-", "subtracted": "-", "minus": "-",
    "power": "^", "to the power": "^", "squared": "^2", "cubed": "^3",
    "equals": "=", "equal": "=", "is": "=",
}


def nlp_to_equation(nlp: str, glossary: Optional[Glossary] = None) -> List[Dict[str, any]]:
    """Convert NLP to equation (retrieval/synthesis).
    
    Args:
        nlp: Natural language description
        glossary: Glossary for symbol lookups (optional)
        
    Returns:
        List of candidate equations with confidence scores
        Each candidate: {"equation": str, "explanation": str, "confidence": float}
    """
    nlp_lower = nlp.lower()
    
    # Extract keywords
    keywords = _extract_keywords(nlp_lower)
    
    # Try template matching first
    candidates = []
    
    # Match against templates
    for template_name, template_info in EQUATION_TEMPLATES.items():
        pattern = template_info["pattern"]
        match_score = _match_pattern(keywords, pattern)
        
        if match_score > 0.5:
            eq_str = template_info["equation"]
            explanation = _generate_explanation(eq_str, glossary)
            candidates.append({
                "equation": eq_str,
                "explanation": explanation,
                "confidence": match_score
            })
            
            # Add alternatives
            if "alternatives" in template_info:
                for alt_eq in template_info["alternatives"]:
                    candidates.append({
                        "equation": alt_eq,
                        "explanation": _generate_explanation(alt_eq, glossary),
                        "confidence": match_score * 0.9
                    })
    
    # Try synthesis if no good template match
    if not candidates or max(c.get("confidence", 0) for c in candidates) < 0.7:
        synthesized = _synthesize_equation(nlp_lower, keywords, glossary)
        if synthesized:
            candidates.extend(synthesized)
    
    # Sort by confidence (descending)
    candidates.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    
    # Return top 3
    return candidates[:3]


def _extract_keywords(nlp: str) -> List[str]:
    """Extract keywords from NLP text.
    
    Args:
        nlp: Natural language text (lowercase)
        
    Returns:
        List of keywords
    """
    # Split into words
    words = re.findall(r'\b\w+\b', nlp)
    
    # Extract phrases (multi-word)
    phrases = []
    for i in range(len(words) - 1):
        phrase = f"{words[i]} {words[i+1]}"
        if phrase in PHRASE_TO_SYMBOL:
            phrases.append(phrase)
    
    # Combine single words and phrases
    keywords = words + phrases
    
    # Filter out common stop words (basic)
    stop_words = {"the", "a", "an", "is", "are", "of", "and", "or", "to", "in"}
    keywords = [k for k in keywords if k not in stop_words and len(k) > 2]
    
    return keywords


def _match_pattern(keywords: List[str], pattern: List[str]) -> float:
    """Match keywords against pattern.
    
    Args:
        keywords: List of keywords
        pattern: Pattern list (required terms)
        
    Returns:
        Match score (0-1)
    """
    keyword_set = set(keywords)
    pattern_lower = [p.lower() for p in pattern]
    
    matches = 0
    for term in pattern_lower:
        # Check if term or synonym appears in keywords
        if term in keyword_set:
            matches += 1
        else:
            # Check for partial matches
            for keyword in keyword_set:
                if term in keyword or keyword in term:
                    matches += 0.5
                    break
    
    return matches / len(pattern) if pattern else 0.0


def _synthesize_equation(nlp: str, keywords: List[str], glossary: Optional[Glossary]) -> List[Dict[str, any]]:
    """Synthesize equation from keywords (basic).
    
    Args:
        nlp: Natural language text
        keywords: Extracted keywords
        glossary: Glossary (optional)
        
    Returns:
        List of synthesized equation candidates
    """
    candidates = []
    
    # Extract symbols from keywords
    symbols = []
    for keyword in keywords:
        if keyword in PHRASE_TO_SYMBOL:
            symbol = PHRASE_TO_SYMBOL[keyword]
            if symbol not in symbols:
                symbols.append(symbol)
    
    # Try to detect operator phrases
    detected_ops = []
    for op_phrase, op_symbol in OPERATOR_PHRASES.items():
        if op_phrase in nlp:
            detected_ops.append(op_symbol)
    
    # If we have symbols and operators, try to build equation
    if len(symbols) >= 2 and "=" in nlp:
        # Simple pattern: "A equals B times C"
        # For now, return empty - synthesis is complex
        pass
    
    return candidates


def _generate_explanation(equation: str, glossary: Optional[Glossary]) -> str:
    """Generate explanation for equation.
    
    Args:
        equation: Equation string
        glossary: Glossary (optional)
        
    Returns:
        Explanation text
    """
    # Use equation_to_nlp if available, otherwise basic description
    from .explain import equation_to_nlp
    return equation_to_nlp(equation, glossary)
