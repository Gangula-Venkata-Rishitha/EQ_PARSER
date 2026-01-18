"""Atomic segmentation: split raw lines into atomic statement segments."""

from typing import List, Tuple
import re
from .pdf_layout import LineMetadata


class Segment:
    """Represents an atomic text segment."""
    
    def __init__(self, text: str, page: int, y_pos: float = 0.0):
        """Initialize segment.
        
        Args:
            text: Cleaned segment text
            page: Page number
            y_pos: Y position on page
        """
        self.text = text.strip()
        self.page = page
        self.y_pos = y_pos
    
    def __repr__(self):
        return f"Segment(page={self.page}, text={self.text[:50]}...)"


def segment_lines(lines: List[LineMetadata]) -> List[Segment]:
    """Split lines into atomic segments.
    
    Splits on:
    - Bullet points: "•", "◦", "-", "*"
    - Multiple assignments: "a = 1  b = 2"
    - Comma-separated assignments: "x1=2,x2=4,x3=6"
    - Logic assignments: "ltl1 = ...  ltl2 = ..."
    - Semicolons
    - Double spaces (artifact splitting)
    
    Repairs split artifacts (segments starting with =, +, *, /, etc.)
    
    Args:
        lines: List of line metadata
        
    Returns:
        List of atomic segments (no fragments starting with operators)
    """
    segments: List[Segment] = []
    
    for line_idx, line in enumerate(lines):
        text = line.text
        
        # Skip empty lines
        if not text.strip():
            continue
        
        # Split by bullets first
        bullet_splits = _split_by_bullets(text)
        
        for bullet_text in bullet_splits:
            # Split comma-separated assignments (x1=2,x2=4)
            comma_splits = _split_comma_assignments(bullet_text)
            
            for comma_text in comma_splits:
                # Split by multiple assignments (pattern: symbol = ... symbol = ...)
                assignment_splits = _split_multi_assignments(comma_text)
                
                for assignment_text in assignment_splits:
                    # Split by semicolon
                    semicolon_splits = _split_by_semicolon(assignment_text)
                    
                    for semicolon_text in semicolon_splits:
                        # Clean up double spaces and artifacts
                        cleaned = _clean_segment(semicolon_text)
                        
                        if cleaned and len(cleaned.strip()) > 0:
                            segments.append(Segment(cleaned, line.page, line.y))
    
    # Repair split artifacts (segments starting with operators)
    segments = _repair_split_artifacts(segments)
    
    return segments


def _split_by_bullets(text: str) -> List[str]:
    """Split text by bullet points.
    
    Args:
        text: Text to split
        
    Returns:
        List of text parts
    """
    # Bullet patterns: •, ◦, -, * (at start or after space)
    bullet_pattern = r'[\s•◦\-\*]+([^\s•◦\-\*].*)'
    matches = list(re.finditer(bullet_pattern, text))
    
    if not matches:
        return [text]
    
    parts = []
    last_end = 0
    
    for match in matches:
        # Text before bullet
        if match.start() > last_end:
            before = text[last_end:match.start()].strip()
            if before:
                parts.append(before)
        
        # Text after bullet
        bullet_text = match.group(1).strip()
        if bullet_text:
            parts.append(bullet_text)
        
        last_end = match.end()
    
    # Remaining text
    if last_end < len(text):
        remaining = text[last_end:].strip()
        if remaining:
            parts.append(remaining)
    
    return parts if parts else [text]


def _split_multi_assignments(text: str) -> List[str]:
    """Split text containing multiple assignments.
    
    Pattern: "a = 1  b = 2" or "ltl1 = ...  ltl2 = ..."
    
    Args:
        text: Text to split
        
    Returns:
        List of individual assignments
    """
    # Pattern: word(s) = ... followed by space(s) and another assignment
    # Look for: symbol = ... (2+ spaces) symbol =
    pattern = r'([a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^=]+?)(\s{2,}|\s+)([a-zA-Z_][a-zA-Z0-9_]*\s*=)'
    
    matches = list(re.finditer(pattern, text))
    
    if not matches:
        return [text]
    
    parts = []
    last_end = 0
    
    for match in matches:
        # First assignment (up to = and value)
        assignment = match.group(1).strip()
        if assignment and last_end < match.start():
            # Add any text before first assignment
            before = text[last_end:match.start()].strip()
            if before:
                parts.append(before)
            parts.append(assignment)
        elif assignment:
            parts.append(assignment)
        
        last_end = match.end(3)  # End of second assignment pattern
    
    # Remaining text (last assignment)
    if last_end < len(text):
        remaining = text[last_end:].strip()
        if remaining:
            parts.append(remaining)
    
    return parts if parts else [text]


def _split_by_semicolon(text: str) -> List[str]:
    """Split text by semicolons.
    
    Args:
        text: Text to split
        
    Returns:
        List of parts
    """
    parts = text.split(';')
    return [p.strip() for p in parts if p.strip()]


def _split_comma_assignments(text: str) -> List[str]:
    """Split comma-separated assignments (e.g., "x1=2,x2=4,x3=6").
    
    Args:
        text: Text to split
        
    Returns:
        List of assignments
    """
    # Pattern: symbol=value,symbol=value
    # But be careful not to split within parentheses or function calls
    parts = []
    current = ""
    paren_depth = 0
    
    for char in text:
        if char == '(':
            paren_depth += 1
            current += char
        elif char == ')':
            paren_depth -= 1
            current += char
        elif char == ',' and paren_depth == 0:
            # Check if this comma is between assignments (has '=' before and after)
            if '=' in current and current.strip():
                parts.append(current.strip())
                current = ""
            else:
                current += char
        else:
            current += char
    
    if current.strip():
        parts.append(current.strip())
    
    return parts if parts else [text]


def _repair_split_artifacts(segments: List[Segment]) -> List[Segment]:
    """Repair split artifacts (segments starting with operators).
    
    If a segment starts with "=", "+", "*", "/", ")", etc., it's likely a split artifact.
    Join it back to the previous segment if possible, else discard.
    
    Args:
        segments: List of segments
        
    Returns:
        List of repaired segments
    """
    if not segments:
        return segments
    
    repaired: List[Segment] = []
    artifact_starters = ['=', '+', '-', '*', '/', ')', ']', '}']
    
    i = 0
    while i < len(segments):
        segment = segments[i]
        text = segment.text.strip()
        
        # Check if segment starts with artifact operator
        if text and text[0] in artifact_starters:
            # Try to join with previous segment if it ends with identifier
            if repaired and repaired[-1].text.strip():
                prev_text = repaired[-1].text.strip()
                # Check if previous ends with identifier/letter
                if prev_text and (prev_text[-1].isalnum() or prev_text[-1] in '_'):
                    # Join them
                    repaired[-1] = Segment(
                        prev_text + ' ' + text,
                        repaired[-1].page,
                        repaired[-1].y_pos
                    )
                    i += 1
                    continue
                # Check if previous ends with '=' (likely LHS missing)
                elif prev_text.endswith('='):
                    # Join them
                    repaired[-1] = Segment(
                        prev_text + ' ' + text,
                        repaired[-1].page,
                        repaired[-1].y_pos
                    )
                    i += 1
                    continue
            
            # Cannot repair - discard fragment (log in debug but don't show to user)
            i += 1
            continue
        
        # Normal segment - keep it
        repaired.append(segment)
        i += 1
    
    return repaired


def _clean_segment(text: str) -> str:
    """Clean segment text.
    
    Args:
        text: Raw text
        
    Returns:
        Cleaned text
    """
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove trailing punctuation artifacts (unless it's part of formula)
    if text and text[-1] in [',', '.'] and '=' not in text:
        # Only remove if it's not a math expression
        if not re.search(r'[+\-*/^()]', text):
            text = text[:-1].strip()
    
    return text
