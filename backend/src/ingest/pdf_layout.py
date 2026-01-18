"""Layout-aware PDF line reconstruction using pdfplumber."""

from typing import List, Dict, Optional
import pdfplumber


class LineMetadata:
    """Metadata for a reconstructed line."""
    
    def __init__(self, text: str, page: int, y: float, x: float = 0.0, 
                 font_size: Optional[float] = None, raw_words: Optional[List] = None):
        """Initialize line metadata.
        
        Args:
            text: Reconstructed line text
            page: Page number (1-indexed)
            y: Y position on page
            x: X position (leftmost) on page
            font_size: Estimated font size (if available)
            raw_words: Raw word objects from pdfplumber
        """
        self.text = text.strip()
        self.page = page
        self.y = y
        self.x = x
        self.font_size = font_size
        self.raw_words = raw_words or []
    
    @property
    def indentation(self) -> float:
        """Get indentation level (x position)."""
        return self.x
    
    @property
    def length(self) -> int:
        """Get line length."""
        return len(self.text)


def extract_lines_from_pdf(pdf_path: str, x_tolerance: float = 3.0, 
                           y_tolerance: float = 5.0) -> List[LineMetadata]:
    """Extract lines from PDF with layout awareness.
    
    Args:
        pdf_path: Path to PDF file
        x_tolerance: Horizontal tolerance for grouping words into lines
        y_tolerance: Vertical tolerance for grouping words
        
    Returns:
        List of LineMetadata objects
    """
    lines: List[LineMetadata] = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # Extract words with layout information
            words = page.extract_words(x_tolerance=x_tolerance, y_tolerance=y_tolerance)
            
            if not words:
                continue
            
            # Group words by Y position (same line)
            y_groups: Dict[float, List[Dict]] = {}
            for word in words:
                # Use y0 (top) as key, rounded to tolerance
                y_key = round(word["top"] / y_tolerance) * y_tolerance
                if y_key not in y_groups:
                    y_groups[y_key] = []
                y_groups[y_key].append(word)
            
            # For each Y group, sort by X and reconstruct line
            for y_pos, word_list in sorted(y_groups.items()):
                # Sort words by x0 (left-to-right)
                word_list.sort(key=lambda w: w.get("x0", 0))
                
                # Reconstruct text
                line_text_parts = []
                for word in word_list:
                    text = word.get("text", "")
                    if text:
                        line_text_parts.append(text)
                
                if not line_text_parts:
                    continue
                
                line_text = " ".join(line_text_parts)
                if not line_text.strip():
                    continue
                
                # Estimate font size (if available)
                font_size = None
                if word_list:
                    # Use average height as proxy for font size
                    heights = [w.get("height", 0) for w in word_list if w.get("height")]
                    if heights:
                        font_size = sum(heights) / len(heights)
                
                # Get leftmost X position
                x_pos = word_list[0].get("x0", 0) if word_list else 0.0
                
                metadata = LineMetadata(
                    text=line_text,
                    page=page_num,
                    y=y_pos,
                    x=x_pos,
                    font_size=font_size,
                    raw_words=word_list
                )
                
                lines.append(metadata)
    
    return lines
