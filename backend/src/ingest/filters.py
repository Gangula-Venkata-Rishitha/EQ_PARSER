"""Noise filtering heuristics for PDF extraction."""

from typing import List, Set
from .pdf_layout import LineMetadata


# Section headers to skip
SECTION_HEADERS: Set[str] = {
    "abstract", "introduction", "references", "acknowledgment", 
    "acknowledgments", "appendix", "conclusion", "conclusions"
}

# Figure caption indicators
FIGURE_CAPTIONS = {"fig.", "figure", "fig", "table", "tab."}


def is_section_header(line: LineMetadata) -> bool:
    """Check if line is a section header.
    
    Args:
        line: Line metadata
        
    Returns:
        True if likely a section header
    """
    text_lower = line.text.lower().strip()
    
    # Check if it's a common section header
    for header in SECTION_HEADERS:
        if text_lower.startswith(header) or text_lower == header:
            return True
    
    # Check formatting: short, possibly centered, often all caps or title case
    if len(text_lower.split()) <= 5:
        # Check if it's a numbered section (e.g., "1. Introduction")
        parts = text_lower.split(".", 1)
        if len(parts) == 2 and parts[0].strip().isdigit():
            if parts[1].strip() in SECTION_HEADERS or len(parts[1].strip()) < 20:
                return True
    
    return False


def is_figure_caption(line: LineMetadata) -> bool:
    """Check if line is a figure caption.
    
    Args:
        line: Line metadata
        
    Returns:
        True if likely a figure caption
    """
    text_lower = line.text.lower()
    
    # Check for figure/table indicators at start
    for indicator in FIGURE_CAPTIONS:
        if text_lower.startswith(indicator):
            return True
    
    return False


def is_long_paragraph(line: LineMetadata, max_words: int = 50) -> bool:
    """Check if line is a long paragraph (likely not math).
    
    Args:
        line: Line metadata
        max_words: Maximum words to consider non-paragraph
        
    Returns:
        True if likely a long paragraph
    """
    word_count = len(line.text.split())
    return word_count > max_words


def has_low_math_density(line: LineMetadata) -> bool:
    """Check if line has low math density (likely prose).
    
    Args:
        line: Line metadata
        
    Returns:
        True if low math density
    """
    text = line.text
    
    # Count math indicators
    math_indicators = ["=", "+", "-", "*", "/", "^", "(", ")", "[", "]", "{", "}", 
                       "∑", "Σ", "∫", "∂", "∇", "√", "≤", "≥", "<", ">"]
    
    math_count = sum(1 for char in text if char in math_indicators)
    total_chars = len(text.replace(" ", ""))
    
    if total_chars == 0:
        return True
    
    math_density = math_count / total_chars
    
    # Low density threshold (less than 5% math chars)
    return math_density < 0.05


def should_skip_line(line: LineMetadata, skip_references: bool = True) -> bool:
    """Determine if line should be skipped based on filtering heuristics.
    
    Args:
        line: Line metadata
        skip_references: Whether to skip lines after "References" section
        
    Returns:
        True if line should be skipped
    """
    # Skip section headers
    if is_section_header(line):
        return True
    
    # Skip figure captions
    if is_figure_caption(line):
        return True
    
    # Skip very long paragraphs (low math density)
    if is_long_paragraph(line) and has_low_math_density(line):
        return True
    
    # Note: references section skipping is handled at block level
    # by tracking when "References" is encountered
    
    return False


def filter_lines(lines: List[LineMetadata], skip_references: bool = True) -> List[LineMetadata]:
    """Filter lines based on noise heuristics.
    
    Args:
        lines: List of line metadata
        skip_references: Whether to skip lines after "References" section
        
    Returns:
        Filtered list of lines
    """
    filtered: List[LineMetadata] = []
    references_encountered = False
    
    for line in lines:
        # Check if we've entered references section
        if skip_references and not references_encountered:
            text_lower = line.text.lower().strip()
            if text_lower.startswith("references") or text_lower == "references":
                references_encountered = True
        
        # Skip everything after references (unless it's clearly math)
        if skip_references and references_encountered:
            # Allow math blocks even after references
            if not has_math_indicators(line):
                continue
        
        # Apply other filters
        if should_skip_line(line, skip_references=False):
            continue
        
        filtered.append(line)
    
    return filtered


def has_math_indicators(line: LineMetadata) -> bool:
    """Check if line has strong math indicators.
    
    Args:
        line: Line metadata
        
    Returns:
        True if line has math indicators
    """
    text = line.text
    math_patterns = ["=", "+", "-", "*", "/", "^", "∑", "Σ", "∫", "∂"]
    return any(pattern in text for pattern in math_patterns)
