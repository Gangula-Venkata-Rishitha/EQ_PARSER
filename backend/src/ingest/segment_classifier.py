"""Strict segment classification: classify segments into exactly one bucket."""

from enum import Enum
from typing import Tuple, Optional
import re


class SegmentType(str, Enum):
    """Segment types."""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    EQUATION = "equation"
    DECLARATION = "declaration"
    INITIALIZATION = "initialization"
    LOGIC_FORMULA = "logic_formula"
    SRS_REQUIREMENT = "srs_requirement"
    UNKNOWN = "unknown"


def classify_segment(text: str) -> Tuple[SegmentType, float]:
    """Classify segment into exactly one type with confidence.
    
    Args:
        text: Segment text
        
    Returns:
        Tuple of (segment_type, confidence 0-1)
    """
    text_lower = text.lower().strip()
    
    # 1. HEADING detection
    if _is_heading(text):
        return SegmentType.HEADING, 0.9
    
    # 2. LOGIC_FORMULA detection (before equation to avoid conflicts)
    logic_confidence = _is_logic_formula(text)
    if logic_confidence > 0.5:
        return SegmentType.LOGIC_FORMULA, logic_confidence
    
    # 3. EQUATION detection
    equation_confidence = _is_equation(text)
    if equation_confidence > 0.5:
        return SegmentType.EQUATION, equation_confidence
    
    # 4. DECLARATION detection
    if _is_declaration(text):
        return SegmentType.DECLARATION, 0.8
    
    # 5. INITIALIZATION detection
    if _is_initialization(text):
        return SegmentType.INITIALIZATION, 0.8
    
    # 6. SRS_REQUIREMENT detection
    srs_confidence = _is_srs_requirement(text)
    if srs_confidence > 0.6:
        return SegmentType.SRS_REQUIREMENT, srs_confidence
    
    # 7. PARAGRAPH detection
    if _is_paragraph(text):
        return SegmentType.PARAGRAPH, 0.7
    
    # 8. Default: UNKNOWN
    return SegmentType.UNKNOWN, 0.3


def _is_heading(text: str) -> bool:
    """Check if segment is a heading.
    
    Args:
        text: Segment text
        
    Returns:
        True if heading
    """
    text_stripped = text.strip()
    
    # Short lines (1-6 words) without '=' and without operators
    word_count = len(text_stripped.split())
    if word_count > 6:
        return False
    
    # Check for '=' - headings usually don't have assignments
    if '=' in text:
        return False
    
    # Check for math operators - headings don't have these
    math_ops = ['+', '-', '*', '/', '^', 'Σ', '∑', '∫', '∂']
    if any(op in text for op in math_ops):
        return False
    
    # ALL CAPS or Title Case (first letter of each word capitalized)
    is_all_caps = text_stripped.isupper() and len([c for c in text_stripped if c.isalpha()]) > 3
    is_title_case = _is_title_case(text_stripped)
    
    return is_all_caps or is_title_case


def _is_title_case(text: str) -> bool:
    """Check if text is in Title Case.
    
    Args:
        text: Text to check
        
    Returns:
        True if title case
    """
    words = text.split()
    if not words:
        return False
    
    # Check if first letter of each word is uppercase
    title_case_count = sum(1 for w in words if w and w[0].isupper())
    return title_case_count >= len(words) * 0.7  # At least 70% title case


def _is_equation(text: str) -> float:
    """Check if segment is a math equation.
    
    Must contain '=' and have math cues in RHS.
    Examples: "ΣF = m * a", "W = F * s", "F12 = −F21"
    
    Args:
        text: Segment text
        
    Returns:
        Confidence score (0-1)
    """
    # Must contain exactly one '=' (after segmentation)
    if text.count('=') != 1:
        return 0.0
    
    # Split into LHS and RHS
    parts = text.split('=', 1)
    if len(parts) < 2:
        return 0.0
    
    lhs = parts[0].strip()
    rhs = parts[1].strip()
    
    if not lhs or not rhs:
        return 0.0
    
    # Exclude logic assignments (ltl1 =, ctl1 =, etc.)
    if re.match(r'^(ltl|ctl|pred|prop)\d+\s*=', text, re.IGNORECASE):
        return 0.0  # This is logic, not equation
    
    # Exclude declarations (RHS is plain words only, no math)
    if _is_declaration(text):
        return 0.0
    
    # Exclude initializations (RHS is just number [+ unit])
    if _is_initialization(text):
        return 0.0  # Let initialization classifier handle it
    
    # Check for math indicators in RHS (STRONG INDICATORS)
    math_indicators = ['+', '-', '*', '/', '^', '**', 'Σ', '∑', '∫', '∂', '√', 'dp/dt']
    has_math_ops = any(op in rhs for op in math_indicators)
    
    # Check for digits and operators together (e.g., "2 * a", "u + a")
    has_digit_ops = bool(re.search(r'\d\s*[+\-*/^]\s*\d', rhs)) or bool(re.search(r'[a-zA-Z]\s*[+\-*/^]\s*[a-zA-Z]', rhs))
    
    # Check for greek letters (often in equations) - μ (mu) for friction
    greek_letters = 'αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ'
    has_greek = any(c in rhs for c in greek_letters)
    
    # Check for summation/index patterns (Σ, ∑, or x_i patterns)
    has_summation = bool(re.search(r'[Σ∑]\s*[^\s=]|x_\d', rhs))
    
    # Check for parentheses with math (e.g., "(1/2)*m*v^2")
    has_math_parens = bool(re.search(r'\([^)]*[+\-*/^][^)]*\)', rhs))
    
    # Check for arithmetic structure (variables and operators)
    # Pattern: letter/number + operator + letter/number
    has_arithmetic = bool(re.search(r'[a-zA-Z0-9]\s*[+\-*/^]\s*[a-zA-Z0-9]', rhs))
    
    score = 0.0
    if has_math_ops:
        score += 0.6  # Strong indicator
    if has_digit_ops:
        score += 0.4
    if has_arithmetic:
        score += 0.3  # Math structure
    if has_greek:
        score += 0.2
    if has_summation:
        score += 0.3
    if has_math_parens:
        score += 0.2
    
    # Lower threshold: if it has math ops OR arithmetic structure, it's likely an equation
    if score > 0.2:
        return min(score, 1.0)
    
    return 0.0


def _is_logic_formula(text: str) -> float:
    """Check if segment is a logic formula (STRICT).
    
    Must contain at least one real logic operator token (not just '=').
    Rejects math equations and declarations.
    
    Args:
        text: Segment text
        
    Returns:
        Confidence score (0-1)
    """
    # STRICT: Must NOT be a math equation (exclude math patterns first)
    math_patterns = ['Σ', '∑', '∫', '∂']
    if any(p in text for p in math_patterns):
        return 0.0  # Summation/integration = math, not logic
    
    # Check for arithmetic operators with numbers (clearly math)
    if re.search(r'\d\s*[+\-*/]\s*\d', text):
        return 0.0  # This is math, not logic
    
    # Check for arithmetic structure with variables (e.g., "m * a", "F * s")
    # Pattern: letter + operator + letter (math-like)
    if re.search(r'\b[a-zA-Z]\s*[*/]\s*[a-zA-Z]\b', text):
        # Check if it's part of an equation (has '=')
        if '=' in text:
            # Check RHS for math structure
            parts = text.split('=', 1)
            if len(parts) > 1:
                rhs = parts[1]
                if re.search(r'[a-zA-Z]\s*[*/]\s*[a-zA-Z]', rhs):
                    return 0.0  # Math equation structure, not logic
    
    # Check for logic assignment pattern: "ltl1 = ...", "ctl1 = ..."
    if re.match(r'^(ltl|ctl|pred|prop)\d+\s*=\s*(.+)', text, re.IGNORECASE):
        # Check if RHS contains logic operators (not just assignment)
        match = re.match(r'^(ltl|ctl|pred|prop)\d+\s*=\s*(.+)', text, re.IGNORECASE)
        if match:
            rhs = match.group(2)
            # Must have logic operators in RHS
            if _has_real_logic_operators(rhs):
                return 0.9  # Very likely logic formula
    
    # Must contain real logic operators (not just '=')
    if not _has_real_logic_operators(text):
        return 0.0
    
    # Check for LTL operators (with word boundaries)
    ltl_ops = r'\b(G|F|X|U|R)\b'
    if re.search(ltl_ops, text):
        # Ensure it's not CTL
        if re.search(r'\b(AG|AX|AF|EX|EF|EG|EU|AU)\b', text):
            return 0.8  # CTL
        return 0.7  # LTL
    
    # Check for CTL operators
    ctl_ops = r'\b(AX|EX|AF|EF|AG|EG|AU|EU)\b'
    if re.search(ctl_ops, text):
        return 0.8
    
    # Check for boolean operators
    bool_ops = r'(\b(and|or|not|implies|iff)\b|∧|∨|¬|→|↔|&|\||!|->|<->)'
    if re.search(bool_ops, text, re.IGNORECASE):
        # Must have propositional structure
        if re.search(r'[a-zA-Z]\s*(and|or|->|<->|∧|∨|→|↔)\s*[a-zA-Z]', text, re.IGNORECASE):
            return 0.7
    
    # Check for quantifiers
    quantifiers = r'(\b(forall|exists|∀|∃)\b)'
    if re.search(quantifiers, text, re.IGNORECASE):
        return 0.7
    
    # Check for CTL/LTL bracket patterns: A[...], E[...]
    if re.search(r'\b(A|E)\s*\[', text, re.IGNORECASE):
        return 0.8
    
    return 0.0


def _has_real_logic_operators(text: str) -> bool:
    """Check if text contains real logic operators (not just '=').
    
    Args:
        text: Text to check
        
    Returns:
        True if contains logic operators
    """
    # LTL operators
    if re.search(r'\b(G|F|X|U|R)\b', text):
        return True
    
    # CTL operators
    if re.search(r'\b(AX|EX|AF|EF|AG|EG|AU|EU)\b', text):
        return True
    
    # Boolean operators
    if re.search(r'(\b(and|or|not|implies|iff)\b|∧|∨|¬|→|↔|&|\||!|->|<->)', text, re.IGNORECASE):
        return True
    
    # Quantifiers
    if re.search(r'(\b(forall|exists|∀|∃)\b)', text, re.IGNORECASE):
        return True
    
    # CTL/LTL bracket patterns
    if re.search(r'\b(A|E)\s*\[', text, re.IGNORECASE):
        return True
    
    return False


def _is_declaration(text: str) -> bool:
    """Check if segment is a variable declaration.
    
    Pattern: symbol = meaning (words only, no math)
    
    Args:
        text: Segment text
        
    Returns:
        True if declaration
    """
    if '=' not in text:
        return False
    
    # Pattern: symbol = words
    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$', text)
    if not match:
        return False
    
    rhs = match.group(2).strip()
    
    # RHS should be mostly words (no math operators)
    math_ops = ['+', '-', '*', '/', '^', '**']
    if any(op in rhs for op in math_ops):
        return False
    
    # Check if RHS is mostly letters/spaces
    letter_count = sum(1 for c in rhs if c.isalpha() or c.isspace())
    total_chars = len(rhs.replace(' ', ''))
    
    if total_chars > 0 and letter_count / total_chars > 0.6:
        return True
    
    return False


def _is_initialization(text: str) -> bool:
    """Check if segment is a variable initialization.
    
    Pattern: symbol = number [unit]
    
    Args:
        text: Segment text
        
    Returns:
        True if initialization
    """
    if '=' not in text:
        return False
    
    # Pattern: symbol = number [unit]
    pattern = r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([0-9]+\.?[0-9]*)\s*(.*)$'
    match = re.match(pattern, text)
    
    if match:
        # Check if unit part is reasonable (optional)
        unit_part = match.group(3).strip() if match.group(3) else ""
        # If unit exists, should be mostly letters/units, not math
        if unit_part and any(op in unit_part for op in ['+', '-', '*', '/']):
            return False
        return True
    
    return False


def _is_srs_requirement(text: str) -> float:
    """Check if segment is an SRS requirement.
    
    Args:
        text: Segment text
        
    Returns:
        Confidence score (0-1)
    """
    text_lower = text.lower()
    
    # Must contain requirement modals
    requirement_modals = ['shall', 'must', 'should', 'required to', 'has to', 
                         'needs to', 'is required', 'when', 'if']
    has_modal = any(modal in text_lower for modal in requirement_modals)
    
    if not has_modal:
        return 0.0
    
    # Exclude if it's a heading
    if _is_heading(text):
        return 0.0
    
    # Exclude very short (likely heading)
    if len(text.split()) < 5:
        return 0.3
    
    # Exclude very long paragraphs (likely narrative)
    if len(text.split()) > 150:
        return 0.3
    
    # Prefer sentences with "system" or imperative structure
    if 'system' in text_lower or 'component' in text_lower:
        return 0.8
    
    # Check requirement density
    modal_count = sum(1 for modal in requirement_modals if modal in text_lower)
    word_count = len(text.split())
    density = modal_count / word_count if word_count > 0 else 0
    
    if density > 0.05:
        return 0.8
    elif density > 0.02:
        return 0.6
    
    return 0.5


def _is_paragraph(text: str) -> bool:
    """Check if segment is a paragraph (prose).
    
    Args:
        text: Segment text
        
    Returns:
        True if paragraph
    """
    # Long text without math/logic indicators
    word_count = len(text.split())
    if word_count < 20:
        return False
    
    # No math operators
    math_ops = ['+', '-', '*', '/', '^', '=', 'Σ', '∑']
    if any(op in text for op in math_ops):
        return False
    
    # No logic operators
    logic_ops = ['G', 'F', 'X', 'U', 'R', 'AX', 'EX', '∧', '∨']
    if any(op in text for op in logic_ops):
        return False
    
    return True
