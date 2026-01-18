"""SRS requirement extraction with tight heuristics."""

from typing import List, Optional, Dict
import re
from ..models.schema import SRSRequirement
from ..ingest.pdf_layout import LineMetadata
from ..logic.logic_parser import LogicFormulaParser
from ..logic.logic_translator import explain_logic_formula


# Requirement modals (strong indicators)
REQUIREMENT_MODALS = {
    "shall", "must", "should", "required to", "has to",
    "needs to", "is required", "will", "may"
}

# Section headers to skip
SKIP_SECTIONS = {
    "abstract", "introduction", "references", "acknowledgment",
    "acknowledgments", "appendix", "conclusion", "conclusions"
}


class SRSExtractor:
    """SRS requirement extractor."""
    
    def __init__(self):
        """Initialize SRS extractor."""
        self.logic_parser = LogicFormulaParser()
    
    def extract_from_lines(self, lines: List[LineMetadata]) -> List[SRSRequirement]:
        """Extract SRS requirements from lines.
        
        Args:
            lines: List of line metadata
            
        Returns:
            List of SRS requirements
        """
        requirements: List[SRSRequirement] = []
        skip_section = False
        
        for i, line in enumerate(lines):
            # Check if we're in a section to skip
            text_lower = line.text.lower().strip()
            if any(text_lower.startswith(section) or text_lower == section for section in SKIP_SECTIONS):
                skip_section = True
                continue
            
            # Reset skip if we leave section
            if skip_section and not self._is_likely_section_header(line):
                # Check if line is far from section header (new section started)
                if i > 0 and not any(s in line.text.lower() for s in SKIP_SECTIONS):
                    skip_section = False
            
            if skip_section:
                continue
            
            # Check if line contains requirement modals
            if self._has_requirement_modal(line.text):
                # Check length gating (avoid very long paragraphs)
                if len(line.text.split()) > 100:  # Very long
                    # Check requirement density
                    modal_count = sum(1 for modal in REQUIREMENT_MODALS if modal in line.text.lower())
                    word_count = len(line.text.split())
                    density = modal_count / word_count if word_count > 0 else 0
                    
                    if density < 0.01:  # Low density
                        continue
                
                # Extract requirement
                req = self._extract_requirement(line, i, lines)
                if req:
                    requirements.append(req)
        
        return requirements
    
    def _has_requirement_modal(self, text: str) -> bool:
        """Check if text contains requirement modal.
        
        Args:
            text: Text to check
            
        Returns:
            True if contains requirement modal
        """
        text_lower = text.lower()
        return any(modal in text_lower for modal in REQUIREMENT_MODALS)
    
    def _is_likely_section_header(self, line: LineMetadata) -> bool:
        """Check if line is likely a section header.
        
        Args:
            line: Line metadata
            
        Returns:
            True if likely section header
        """
        text = line.text.strip()
        # Short lines are more likely to be headers
        return len(text.split()) <= 5
    
    def _extract_requirement(self, line: LineMetadata, line_idx: int, 
                            all_lines: List[LineMetadata]) -> Optional[SRSRequirement]:
        """Extract single requirement from line.
        
        Args:
            line: Line metadata
            line_idx: Index in lines list
            all_lines: All lines (for context)
            
        Returns:
            SRS requirement if extracted, None otherwise
        """
        requirement_text = line.text.strip()
        
        # Try to extract linked logic (same line after ":" or next 1-3 lines)
        linked_logic = None
        
        # Check same line for logic after ":"
        if ":" in requirement_text:
            parts = requirement_text.split(":", 1)
            if len(parts) > 1:
                after_colon = parts[1].strip()
                logic_data = self._try_parse_logic(after_colon)
                if logic_data and logic_data["is_valid"]:
                    linked_logic = self._create_logic_formula(logic_data, line.page)
        
        # Check next 1-3 lines for logic
        if not linked_logic:
            for offset in [1, 2, 3]:
                if line_idx + offset < len(all_lines):
                    next_line = all_lines[line_idx + offset]
                    logic_data = self._try_parse_logic(next_line.text)
                    if logic_data and logic_data["is_valid"]:
                        linked_logic = self._create_logic_formula(logic_data, next_line.page)
                        break
        
        # Generate requirement ID
        req_id = f"req-{line_idx:04d}"
        
        # Generate explanation
        explanation = self._generate_explanation(requirement_text, linked_logic)
        
        # Extract dependency mapping from linked logic
        dependency_mapping: Dict[str, List[str]] = {}
        if linked_logic:
            dependency_mapping = linked_logic.dependency_mapping
        
        return SRSRequirement(
            req_id=req_id,
            page=line.page,
            requirement_text=requirement_text,
            linked_logic=linked_logic,
            explanation=explanation,
            dependency_mapping=dependency_mapping
        )
    
    def _try_parse_logic(self, text: str) -> Optional[Dict]:
        """Try to parse text as logic formula.
        
        Args:
            text: Text to parse
            
        Returns:
            Parsed logic data if successful, None otherwise
        """
        # Check for logic indicators
        logic_indicators = ["∧", "∨", "¬", "→", "↔", "G", "F", "X", "U", "R",
                           "AX", "EX", "AF", "EF", "AG", "EG", "AU", "EU",
                           "∀", "∃", "AND", "OR", "NOT", "implies"]
        
        if not any(indicator in text for indicator in logic_indicators):
            return None
        
        try:
            logic_data = self.logic_parser.parse(text)
            return logic_data
        except Exception:
            return None
    
    def _create_logic_formula(self, logic_data: Dict, page: int):
        """Create LogicFormula from parsed data.
        
        Args:
            logic_data: Parsed logic data
            page: Page number
            
        Returns:
            LogicFormula object
        """
        from ..models.schema import LogicFormula
        
        return LogicFormula(
            formula_id=f"logic-{hash(logic_data['raw']) % 10000:04d}",
            page=page,
            raw=logic_data["raw"],
            normalized=logic_data["normalized"],
            logic_type=logic_data["logic_type"],
            form=logic_data["form"],
            is_valid=logic_data["is_valid"],
            syntax_errors=logic_data["syntax_errors"],
            explanation_nlp=explain_logic_formula(logic_data),
            dependency_mapping=logic_data["dependency_mapping"]
        )
    
    def _generate_explanation(self, requirement_text: str, linked_logic) -> str:
        """Generate explanation for requirement.
        
        Args:
            requirement_text: Requirement text
            linked_logic: Linked logic formula (optional)
            
        Returns:
            Explanation text
        """
        explanation = requirement_text
        
        if linked_logic:
            explanation += f" Linked logic: {linked_logic.explanation_nlp}"
        
        return explanation
