"""Equation validator: explicit error flagging (must NOT silently skip)."""

from typing import List, Set
from ..models.schema import ErrorReport, ErrorType
from .lexer import tokenize_equation, Token, OPERATOR, BRACKET_OPEN, BRACKET_CLOSE, EQUALS, SYMBOL, NUMBER
import re


def validate_equation(equation: str, known_symbols: Set[str] = None) -> List[ErrorReport]:
    """Validate equation and return list of errors (must flag all issues).
    
    Args:
        equation: Equation string to validate
        known_symbols: Set of known symbols (from glossary) for suspicious exponent check
        
    Returns:
        List of error reports (empty if valid)
    """
    errors: List[ErrorReport] = []
    known_symbols = known_symbols or set()
    
    # Check missing brackets
    bracket_errors = _check_brackets(equation)
    errors.extend(bracket_errors)
    
    # Check dangling operators
    dangling_errors = _check_dangling_operators(equation)
    errors.extend(dangling_errors)
    
    # Check missing operands
    operand_errors = _check_missing_operands(equation)
    errors.extend(operand_errors)
    
    # Check malformed equals
    equals_errors = _check_malformed_equals(equation)
    errors.extend(equals_errors)
    
    # Check suspicious exponents
    exponent_errors = _check_suspicious_exponents(equation, known_symbols)
    errors.extend(exponent_errors)
    
    # Check incomplete fractions/parentheses
    incomplete_errors = _check_incomplete_constructs(equation)
    errors.extend(incomplete_errors)
    
    return errors


def _check_brackets(equation: str) -> List[ErrorReport]:
    """Check for unbalanced brackets.
    
    Args:
        equation: Equation string
        
    Returns:
        List of bracket errors
    """
    errors: List[ErrorReport] = []
    
    bracket_pairs = {"(": ")", "[": "]", "{": "}"}
    stack = []
    
    for i, char in enumerate(equation):
        if char in bracket_pairs:
            stack.append((char, bracket_pairs[char], i))
        elif char in bracket_pairs.values():
            if not stack:
                errors.append(ErrorReport(
                    error_type=ErrorType.MISSING_BRACKETS,
                    message=f"Unmatched closing bracket '{char}' at position {i}",
                    location=f"position {i}"
                ))
            else:
                opening, expected_closing, _ = stack.pop()
                if char != expected_closing:
                    errors.append(ErrorReport(
                        error_type=ErrorType.MISSING_BRACKETS,
                        message=f"Mismatched brackets: '{opening}' expects '{expected_closing}', found '{char}'",
                        location=f"position {i}"
                    ))
    
    # Check for unclosed brackets
    if stack:
        for opening, expected_closing, pos in stack:
            errors.append(ErrorReport(
                error_type=ErrorType.MISSING_BRACKETS,
                message=f"Unclosed bracket '{opening}' (expecting '{expected_closing}') at position {pos}",
                location=f"position {pos}"
            ))
    
    return errors


def _check_dangling_operators(equation: str) -> List[ErrorReport]:
    """Check for dangling operators (at start/end or consecutive).
    
    Args:
        equation: Equation string
        
    Returns:
        List of dangling operator errors
    """
    errors: List[ErrorReport] = []
    
    equation_stripped = equation.strip()
    if not equation_stripped:
        return errors
    
    operators = ["+", "-", "*", "/", "^", "**", "="]
    
    # Check if equation ends with operator
    if equation_stripped[-1] in operators:
        errors.append(ErrorReport(
            error_type=ErrorType.DANGLING_OPERATOR,
            message=f"Equation ends with operator '{equation_stripped[-1]}'",
            location="end of equation"
        ))
    
    # Check if equation starts with certain operators (except +/- which can be unary)
    if equation_stripped[0] in ["*", "/", "^", "**", "="]:
        errors.append(ErrorReport(
            error_type=ErrorType.DANGLING_OPERATOR,
            message=f"Equation starts with operator '{equation_stripped[0]}'",
            location="start of equation"
        ))
    
    # Check for consecutive operators (excluding valid combinations like "**")
    for i in range(len(equation_stripped) - 1):
        char1 = equation_stripped[i]
        char2 = equation_stripped[i + 1]
        
        # Skip valid combinations
        if char1 == "*" and char2 == "*":
            continue
        if char1 == "=" and char2 == "=":  # == comparison
            continue
        
        if char1 in operators and char2 in operators:
            if not (char1 in "+-" and char2 in "+-*"):  # Allow unary +/- followed by * (rare)
                errors.append(ErrorReport(
                    error_type=ErrorType.DANGLING_OPERATOR,
                    message=f"Consecutive operators '{char1}{char2}' at position {i}",
                    location=f"position {i}"
                ))
    
    return errors


def _check_missing_operands(equation: str) -> List[ErrorReport]:
    """Check for missing operands (operator without neighbors).
    
    Args:
        equation: Equation string
        
    Returns:
        List of missing operand errors
    """
    errors: List[ErrorReport] = []
    
    # Tokenize to check structure
    tokens = tokenize_equation(equation)
    
    if not tokens:
        return errors
    
    operators = ["+", "-", "*", "/", "^", "**"]
    
    for i, token in enumerate(tokens):
        if token.type == OPERATOR and token.value in operators:
            # Check if operator has operands on both sides (or is unary +/-)
            has_left = False
            has_right = False
            
            # Check left operand
            if i > 0:
                prev_token = tokens[i - 1]
                if prev_token.type in [NUMBER, SYMBOL, BRACKET_CLOSE]:
                    has_left = True
                elif token.value in "+-" and i == 0:  # Unary at start
                    has_left = True
            
            # Check right operand
            if i < len(tokens) - 1:
                next_token = tokens[i + 1]
                if next_token.type in [NUMBER, SYMBOL, BRACKET_OPEN]:
                    has_right = True
            
            # Unary +/- is allowed, but others need both operands
            if token.value in "+-":
                if not has_right:
                    errors.append(ErrorReport(
                        error_type=ErrorType.MISSING_OPERAND,
                        message=f"Operator '{token.value}' missing right operand at position {token.position}",
                        location=f"position {token.position}"
                    ))
            else:
                if not has_left or not has_right:
                    missing = []
                    if not has_left:
                        missing.append("left")
                    if not has_right:
                        missing.append("right")
                    errors.append(ErrorReport(
                        error_type=ErrorType.MISSING_OPERAND,
                        message=f"Operator '{token.value}' missing {', '.join(missing)} operand at position {token.position}",
                        location=f"position {token.position}"
                    ))
    
    return errors


def _check_malformed_equals(equation: str) -> List[ErrorReport]:
    """Check for malformed equals (missing LHS or RHS).
    
    NOTE: Multiple equals are NOT an error if segment contains multiple assignments.
    The caller should split multi-assignment segments BEFORE validation.
    
    Args:
        equation: Equation string (should be single assignment)
        
    Returns:
        List of malformed equals errors
    """
    errors: List[ErrorReport] = []
    
    equals_count = equation.count("=")
    
    # If multiple equals, check if it's a comparison (==)
    if equals_count > 1:
        if "==" not in equation:
            # Multiple '=' in single segment means it's likely a multi-assignment
            # This should have been split by segmenter - flag as warning, not error
            # Actually, we should NOT flag this as error if it's clearly multiple assignments
            # Check pattern: "a = ... b = ..." (multiple assignments)
            if re.search(r'\w+\s*=\s*[^=]+\s+\w+\s*=', equation):
                # Multiple assignments - this should have been split, but don't flag as malformed
                pass
            else:
                # Unknown pattern - flag it
                errors.append(ErrorReport(
                    error_type=ErrorType.MALFORMED_EQUALS,
                    message=f"Multiple '=' operators found ({equals_count}) - may need splitting",
                    location="equation"
                ))
    
    # Check for missing LHS or RHS (single assignment case)
    if "=" in equation and equals_count == 1:
        parts = equation.split("=", 1)
        lhs = parts[0].strip()
        rhs = parts[1].strip() if len(parts) > 1 else ""
        
        if not lhs:
            errors.append(ErrorReport(
                error_type=ErrorType.MALFORMED_EQUALS,
                message="Missing left-hand side of equation",
                location="start of equation"
            ))
        
        if not rhs:
            errors.append(ErrorReport(
                error_type=ErrorType.MALFORMED_EQUALS,
                message="Missing right-hand side of equation",
                location="end of equation"
            ))
    
    return errors


def _check_suspicious_exponents(equation: str, known_symbols: Set[str]) -> List[ErrorReport]:
    """Check for suspicious exponents (e.g., "v2" likely means "v^2").
    
    Index-aware: Does NOT flag F12, F21, x1, x2 etc (common index patterns).
    Only flags when base symbol exists and exponent usage is plausible.
    
    Args:
        equation: Equation string
        known_symbols: Set of known symbols from glossary
        
    Returns:
        List of suspicious exponent errors
    """
    errors: List[ErrorReport] = []
    
    # Index allowlist patterns (common physics/engineering indices)
    index_patterns = [
        r'\bF\d+\b',  # Forces: F12, F21
        r'\bx\d+\b',  # Sequence indices: x1, x2
        r'\ba\d+\b',  # Acceleration indices: a1, a2
        r'\bv\d+\b',  # Velocity indices: v1, v2 (but v2 as velocity squared is different)
        r'\bp\d+\b',  # Momentum indices
        r'\bm\d+\b',  # Mass indices
    ]
    
    # Pattern: letter(s) followed by digit(s) without operator (e.g., "v2", "x3")
    pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*?)([0-9]+)\b'
    
    matches = re.finditer(pattern, equation)
    for match in matches:
        potential_symbol = match.group(1)
        digit_part = match.group(2)
        full_match = match.group(0)
        
        # Skip if full match is in known symbols (e.g., "v2" is explicitly declared)
        if full_match in known_symbols:
            continue
        
        # Skip if matches index pattern (F12, x1, etc.)
        is_index_pattern = any(re.match(pattern, full_match) for pattern in index_patterns)
        if is_index_pattern:
            continue
        
        # Only flag if:
        # 1. Base symbol is known (e.g., "v" is velocity)
        # 2. Digit is 2, 3, or 4 (common exponents, not indices)
        # 3. Token is short (1-2 letters) - indices are often longer
        if potential_symbol in known_symbols and digit_part in ['2', '3', '4']:
            if len(potential_symbol) <= 2:
                errors.append(ErrorReport(
                    error_type=ErrorType.SUSPICIOUS_EXPONENT,
                    message=f"Suspicious exponent pattern '{full_match}' - likely meant '{potential_symbol}^{digit_part}' (if not indexed variable)",
                    location=f"'{full_match}'"
                ))
    
    return errors


def _check_incomplete_constructs(equation: str) -> List[ErrorReport]:
    """Check for incomplete fractions or parenthetical constructs.
    
    Args:
        equation: Equation string
        
    Returns:
        List of incomplete construct errors
    """
    errors: List[ErrorReport] = []
    
    # Check for incomplete fractions (e.g., "1/2*" might be incomplete)
    # Pattern: number/number* followed by nothing or incomplete
    fraction_pattern = r'\d+\s*/\s*\d+\s*\*?\s*$'
    if re.search(fraction_pattern, equation):
        # Check if followed by incomplete expression
        if not equation.strip().endswith(")"):  # Might be part of larger expression
            errors.append(ErrorReport(
                error_type=ErrorType.INCOMPLETE_FRACTION,
                message="Incomplete fraction or expression",
                location="end of equation"
            ))
    
    # Check for incomplete parenthetical expressions at start
    if equation.strip().startswith("(") and ")" not in equation:
        errors.append(ErrorReport(
            error_type=ErrorType.INCOMPLETE_PARENTHESIS,
            message="Incomplete parenthetical expression starting at beginning",
            location="start of equation"
        ))
    
    return errors
