"""Math block detection and multiline equation merging."""

from typing import List, Optional, Tuple
from .pdf_layout import LineMetadata
import re


class MathBlock:
    """Represents a detected math block (may be multiline)."""
    
    def __init__(self, lines: List[LineMetadata], label: Optional[str] = None):
        """Initialize math block.
        
        Args:
            lines: Lines that make up this block
            label: Equation label/number (e.g., "(1)")
        """
        self.lines = lines
        self.label = label
        self.page = lines[0].page if lines else 1
    
    @property
    def text(self) -> str:
        """Get combined text of all lines."""
        return " ".join(line.text for line in self.lines)
    
    @property
    def raw_text(self) -> str:
        """Get raw combined text (preserving structure)."""
        return "\n".join(line.text for line in self.lines)


def score_line_math_density(line: LineMetadata) -> float:
    """Score line for math density (0-1).
    
    Args:
        line: Line metadata
        
    Returns:
        Math density score
    """
    text = line.text
    
    # Binary indicators (strong math)
    has_equals = "=" in text
    operator_count = sum(1 for op in ["+", "-", "*", "/", "^", "**"] if op in text)
    
    # Character ratios
    symbol_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_")
    digit_chars = set("0123456789")
    bracket_chars = set("()[]{}")
    
    symbol_count = sum(1 for c in text if c in symbol_chars)
    digit_count = sum(1 for c in text if c in digit_chars)
    bracket_count = sum(1 for c in text if c in bracket_chars)
    
    total_chars = len(text.replace(" ", ""))
    if total_chars == 0:
        return 0.0
    
    symbol_ratio = symbol_count / total_chars
    digit_ratio = digit_count / total_chars
    bracket_ratio = bracket_count / total_chars
    
    # Greek/unicode math
    greek_unicode = "αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
    unicode_math = "∑Σ∫∂∇√≤≥≠≈±∞∏"
    unicode_count = sum(1 for c in text if c in greek_unicode or c in unicode_math)
    unicode_ratio = unicode_count / total_chars if total_chars > 0 else 0.0
    
    # Weighted score
    score = 0.0
    if has_equals:
        score += 0.3
    score += min(operator_count * 0.1, 0.2)
    score += min(symbol_ratio * 2.0, 0.2)
    score += min(digit_ratio * 2.0, 0.15)
    score += min(bracket_ratio * 2.0, 0.1)
    score += min(unicode_ratio * 5.0, 0.05)
    
    return min(score, 1.0)


def has_unclosed_brackets(text: str) -> bool:
    """Check if text has unclosed brackets.
    
    Args:
        text: Text to check
        
    Returns:
        True if brackets are unclosed
    """
    bracket_pairs = {"(": ")", "[": "]", "{": "}"}
    stack = []
    
    for char in text:
        if char in bracket_pairs:
            stack.append(bracket_pairs[char])
        elif char in bracket_pairs.values():
            if not stack or stack.pop() != char:
                return True
    
    return len(stack) > 0


def ends_with_operator(text: str) -> bool:
    """Check if text ends with an operator.
    
    Args:
        text: Text to check
        
    Returns:
        True if ends with operator
    """
    text_stripped = text.strip()
    if not text_stripped:
        return False
    
    operators = ["+", "-", "*", "/", "^", "**", "=", "±", "×", "÷"]
    return any(text_stripped.endswith(op) for op in operators)


def extract_equation_label(text: str) -> Tuple[Optional[str], str]:
    """Extract equation label from text (e.g., "(1)" at end).
    
    Args:
        text: Text potentially containing label
        
    Returns:
        Tuple of (label, text_without_label)
    """
    # Pattern for equation numbers: (1), (2), etc. at end or on right side
    label_pattern = r'\s*\((\d+)\)\s*$'
    match = re.search(label_pattern, text)
    
    if match:
        label = f"({match.group(1)})"
        text_cleaned = re.sub(label_pattern, "", text).strip()
        return label, text_cleaned
    
    # Also check for standalone patterns like "Equation (1)" or "Eq. 1"
    eq_patterns = [
        r'\s+\(Eq\.?\s*(\d+)\)',
        r'\s+Equation\s+\((\d+)\)',
    ]
    
    for pattern in eq_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            label = f"({match.group(1)})"
            text_cleaned = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
            return label, text_cleaned
    
    return None, text


def should_merge_lines(line1: LineMetadata, line2: LineMetadata) -> bool:
    """Determine if two lines should be merged (multiline equation).
    
    Args:
        line1: First line
        line2: Second line
        
    Returns:
        True if lines should be merged
    """
    text1 = line1.text
    text2 = line2.text
    
    # Merge if first line has unclosed brackets
    if has_unclosed_brackets(text1):
        return True
    
    # Merge if first line ends with operator
    if ends_with_operator(text1):
        return True
    
    # Merge if second line is indented and math-dense (continuation)
    if line2.indentation > line1.indentation + 5:  # Significant indentation
        score2 = score_line_math_density(line2)
        if score2 > 0.3:  # Math-dense
            return True
    
    # Merge if both lines are math-dense and on same page
    if line1.page == line2.page:
        score1 = score_line_math_density(line1)
        score2 = score_line_math_density(line2)
        if score1 > 0.4 and score2 > 0.4:
            # Check proximity (within reasonable Y distance)
            y_diff = abs(line2.y - line1.y)
            if y_diff < 30:  # Reasonable line spacing
                return True
    
    return False


def detect_math_blocks(lines: List[LineMetadata], min_score: float = 0.2) -> List[MathBlock]:
    """Detect math blocks from lines.
    
    Args:
        lines: List of line metadata
        min_score: Minimum math density score to consider
        
    Returns:
        List of detected math blocks
    """
    blocks: List[MathBlock] = []
    current_block_lines: List[LineMetadata] = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        score = score_line_math_density(line)
        
        # Start new block if score is high enough
        if score >= min_score:
            current_block_lines = [line]
            
            # Try to merge subsequent lines
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                
                if should_merge_lines(current_block_lines[-1], next_line):
                    current_block_lines.append(next_line)
                    j += 1
                else:
                    break
            
            # Extract label from combined text
            combined_text = " ".join(l.text for l in current_block_lines)
            label, _ = extract_equation_label(combined_text)
            
            block = MathBlock(current_block_lines, label)
            blocks.append(block)
            
            i = j
        else:
            i += 1
    
    return blocks
