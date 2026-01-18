"""Math tokenizer for equation parsing."""

from typing import List, Tuple
import re


class Token:
    """Represents a token in an equation."""
    
    def __init__(self, token_type: str, value: str, position: int):
        """Initialize token.
        
        Args:
            token_type: Type of token (NUMBER, SYMBOL, OPERATOR, etc.)
            value: Token value
            position: Position in source string
        """
        self.type = token_type
        self.value = value
        self.position = position
    
    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, {self.position})"


# Token types
NUMBER = "NUMBER"
SYMBOL = "SYMBOL"
OPERATOR = "OPERATOR"
BRACKET_OPEN = "BRACKET_OPEN"
BRACKET_CLOSE = "BRACKET_CLOSE"
EQUALS = "EQUALS"
WHITESPACE = "WHITESPACE"


def tokenize_equation(equation: str) -> List[Token]:
    """Tokenize equation string.
    
    Args:
        equation: Equation string
        
    Returns:
        List of tokens
    """
    tokens: List[Token] = []
    i = 0
    
    while i < len(equation):
        char = equation[i]
        
        # Skip whitespace (but keep for position tracking)
        if char.isspace():
            i += 1
            continue
        
        # Number (including decimals)
        if char.isdigit() or char == '.':
            start = i
            while i < len(equation) and (equation[i].isdigit() or equation[i] == '.'):
                i += 1
            value = equation[start:i]
            tokens.append(Token(NUMBER, value, start))
            continue
        
        # Operators
        if char in "+-*/^":
            tokens.append(Token(OPERATOR, char, i))
            i += 1
            continue
        
        # Exponentiation
        if i + 1 < len(equation) and equation[i:i+2] == "**":
            tokens.append(Token(OPERATOR, "**", i))
            i += 2
            continue
        
        # Equals
        if char == '=':
            tokens.append(Token(EQUALS, char, i))
            i += 1
            continue
        
        # Brackets
        if char in '([{':
            tokens.append(Token(BRACKET_OPEN, char, i))
            i += 1
            continue
        
        if char in ')]}':
            tokens.append(Token(BRACKET_CLOSE, char, i))
            i += 1
            continue
        
        # Symbol (variable/function name)
        if char.isalpha() or char == '_':
            start = i
            while i < len(equation) and (equation[i].isalnum() or equation[i] == '_'):
                i += 1
            value = equation[start:i]
            tokens.append(Token(SYMBOL, value, i))
            continue
        
        # Unknown character - skip or error?
        i += 1
    
    return tokens


def extract_symbols(equation: str) -> List[str]:
    """Extract all symbols from equation.
    
    Args:
        equation: Equation string
        
    Returns:
        List of unique symbols
    """
    tokens = tokenize_equation(equation)
    symbols = set()
    
    for token in tokens:
        if token.type == SYMBOL:
            symbols.add(token.value)
    
    return sorted(list(symbols))
