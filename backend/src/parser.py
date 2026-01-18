"""Main parser orchestrator - coordinates all extraction modules (REFACTORED with segmentation)."""

from typing import List, Dict, Set, Tuple, Optional
import hashlib
from pathlib import Path
import re

from .ingest.pdf_layout import extract_lines_from_pdf, LineMetadata
from .ingest.filters import filter_lines
from .ingest.segmenter import segment_lines, Segment
from .ingest.segment_classifier import classify_segment, SegmentType
from .glossary.glossary import Glossary
from .math.normalize import normalize_equation
from .math.validator import validate_equation
from .math.lexer import extract_symbols
from .math.classifier import classify_equation
from .math.explain import equation_to_nlp
from .logic.logic_parser import LogicFormulaParser
from .logic.logic_translator import explain_logic_formula
from .models.schema import (
    ParseResult, Equation, LogicFormula, SRSRequirement, Summary,
    EquationType, LogicType, VariableStatus, ErrorReport
)


class Parser:
    """Main parser orchestrator (refactored with segmentation)."""
    
    def __init__(self):
        """Initialize parser."""
        self.logic_parser = LogicFormulaParser()
    
    def parse_pdf(self, pdf_path: str) -> ParseResult:
        """Parse PDF and extract all components using segmentation + classification.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            ParseResult with all extracted data
        """
        # Generate document ID
        file_name = Path(pdf_path).name
        doc_id = self._generate_doc_id(pdf_path)
        
        # Step 1: Extract lines with layout awareness
        lines = extract_lines_from_pdf(pdf_path)
        if not lines:
            return self._create_empty_result(doc_id, file_name, 0)
        
        # Step 2: Filter noise
        filtered_lines = filter_lines(lines)
        
        # Step 3: Segment into atomic statements
        segments = segment_lines(filtered_lines)
        
        # Step 4: Classify segments (strict gating - only keep EQUATION/DECLARATION/INITIALIZATION/LOGIC_FORMULA/SRS_REQUIREMENT)
        classified_segments = self._classify_segments(segments)
        
        # Step 5: Extract glossary (from DECLARATION and INITIALIZATION segments)
        glossary = Glossary()
        decl_init_lines = []
        for segment, seg_type in classified_segments:
            if seg_type in [SegmentType.DECLARATION, SegmentType.INITIALIZATION]:
                # Convert segment to LineMetadata for glossary extraction
                line_meta = LineMetadata(segment.text, segment.page, segment.y_pos)
                decl_init_lines.append(line_meta)
        if decl_init_lines:
            glossary.extract_from_lines(decl_init_lines)
        
        # Step 6: Extract equations (only from EQUATION segments)
        equation_segments = [(s, t) for s, t in classified_segments if t == SegmentType.EQUATION]
        equations = self._extract_equations_from_segments(equation_segments, glossary)
        
        # Step 7: Extract logic formulas (only from LOGIC_FORMULA segments)
        logic_segments = [(s, t) for s, t in classified_segments if t == SegmentType.LOGIC_FORMULA]
        logic_formulas = self._extract_logic_formulas_from_segments(logic_segments)
        
        # Step 8: Extract SRS requirements (from SRS_REQUIREMENT segments)
        srs_segments = [(s, t) for s, t in classified_segments if t == SegmentType.SRS_REQUIREMENT]
        srs_requirements = self._extract_srs_from_segments(srs_segments, logic_formulas)
        
        # Step 9: Build summary
        summary = self._build_summary(equations, logic_formulas, srs_requirements, glossary)
        
        # Step 10: Collect all errors
        all_errors = self._collect_errors(equations, logic_formulas)
        
        # Count pages
        pages = max([line.page for line in lines], default=1)
        
        return ParseResult(
            doc_id=doc_id,
            file_name=file_name,
            pages=pages,
            summary=summary,
            glossary=glossary.to_dict(),
            equations=equations,
            logic_formulas=logic_formulas,
            srs_requirements=srs_requirements,
            errors=all_errors
        )
    
    def _classify_segments(self, segments: List[Segment]) -> List[Tuple[Segment, SegmentType]]:
        """Classify segments and return only kept types.
        
        Args:
            segments: List of segments
            
        Returns:
            List of (segment, type) tuples for kept segments
        """
        classified = []
        for segment in segments:
            seg_type, confidence = classify_segment(segment.text)
            
            # Only keep: EQUATION, DECLARATION, INITIALIZATION, LOGIC_FORMULA, SRS_REQUIREMENT
            if seg_type in [SegmentType.EQUATION, SegmentType.DECLARATION, SegmentType.INITIALIZATION,
                           SegmentType.LOGIC_FORMULA, SegmentType.SRS_REQUIREMENT]:
                classified.append((segment, seg_type))
        
        return classified
    
    def _extract_equations_from_segments(self, equation_segments: List[Tuple[Segment, SegmentType]], glossary: Glossary) -> List[Equation]:
        """Extract equations from EQUATION segments.
        
        Args:
            equation_segments: List of (segment, type) tuples
            glossary: Glossary for variable status
            
        Returns:
            List of extracted equations
        """
        equations: List[Equation] = []
        known_symbols = set(glossary.get_declared_symbols() + glossary.get_initialized_symbols())
        
        for idx, (segment, _) in enumerate(equation_segments):
            raw_text = segment.text
            
            # Split if multiple assignments remain (should have been split by segmenter, but double-check)
            if raw_text.count('=') > 1 and '==' not in raw_text:
                # Split into individual assignments
                assignments = self._split_assignments(raw_text)
            else:
                assignments = [raw_text]
            
            for assignment in assignments:
                eq_id = f"eq-{len(equations) + 1:04d}"
                
                # Normalize equation
                normalized = normalize_equation(assignment)
                
                # Validate equation (MUST flag errors, never skip silently)
                errors = validate_equation(normalized, known_symbols)
                
                # Extract symbols
                used_symbols = extract_symbols(normalized)
                
                # Build variable status
                variable_status = self._build_variable_status(used_symbols, glossary)
                
                # Classify equation
                eq_type, confidence = classify_equation(normalized, used_symbols)
                
                # Generate explanation
                explanation = equation_to_nlp(normalized, glossary)
                
                # Extract label (e.g., "(1)") from raw text
                label = self._extract_label(raw_text)
                
                equation = Equation(
                    eq_id=eq_id,
                    page=segment.page,
                    label=label,
                    raw=assignment,
                    normalized=normalized,
                    type=eq_type,
                    confidence=confidence,
                    explanation_nlp=explanation,
                    variables=variable_status,
                    errors=errors
                )
                
                equations.append(equation)
        
        return equations
    
    def _split_assignments(self, text: str) -> List[str]:
        """Split text with multiple assignments.
        
        Args:
            text: Text with multiple assignments
            
        Returns:
            List of individual assignments
        """
        # Pattern: symbol = ... followed by space and another symbol =
        pattern = r'([a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^=]+?)(\s{2,}|\s+)([a-zA-Z_][a-zA-Z0-9_]*\s*=)'
        parts = []
        last_end = 0
        
        for match in re.finditer(pattern, text):
            if match.start() > last_end:
                parts.append(text[last_end:match.start()].strip())
            parts.append(match.group(1).strip())
            last_end = match.end(3)
        
        if last_end < len(text):
            parts.append(text[last_end:].strip())
        
        return [p for p in parts if p]
    
    def _extract_label(self, text: str) -> Optional[str]:
        """Extract equation label from text.
        
        Args:
            text: Text potentially containing label
            
        Returns:
            Label string if found, None otherwise
        """
        match = re.search(r'\((\d+)\)\s*$', text)
        if match:
            return f"({match.group(1)})"
        return None
    
    def _extract_logic_formulas_from_segments(self, logic_segments: List[Tuple[Segment, SegmentType]]) -> List[LogicFormula]:
        """Extract logic formulas from LOGIC_FORMULA segments.
        
        Args:
            logic_segments: List of (segment, type) tuples
            
        Returns:
            List of extracted logic formulas
        """
        logic_formulas: List[LogicFormula] = []
        
        for idx, (segment, _) in enumerate(logic_segments):
            text = segment.text.strip()
            
            try:
                logic_data = self.logic_parser.parse(text)
                
                formula_id = f"logic-{idx + 1:04d}"
                explanation = explain_logic_formula(logic_data)
                
                logic_formula = LogicFormula(
                    formula_id=formula_id,
                    page=segment.page,
                    raw=logic_data["raw"],
                    normalized=logic_data["normalized"],
                    logic_type=logic_data["logic_type"],
                    form=logic_data["form"],
                    is_valid=logic_data["is_valid"],
                    syntax_errors=logic_data["syntax_errors"],
                    explanation_nlp=explanation,
                    dependency_mapping=logic_data["dependency_mapping"]
                )
                
                logic_formulas.append(logic_formula)
            except Exception:
                # Continue on parsing error
                continue
        
        return logic_formulas
    
    def _extract_srs_from_segments(self, srs_segments: List[Tuple[Segment, SegmentType]], logic_formulas: List[LogicFormula]) -> List[SRSRequirement]:
        """Extract SRS requirements from SRS_REQUIREMENT segments.
        
        Args:
            srs_segments: List of (segment, type) tuples
            logic_formulas: List of logic formulas (for linking)
            
        Returns:
            List of SRS requirements
        """
        requirements: List[SRSRequirement] = []
        
        for idx, (segment, _) in enumerate(srs_segments):
            req_id = f"req-{idx + 1:04d}"
            requirement_text = segment.text.strip()
            
            # Find nearest logic formula (within same page, ±3 segments by position)
            linked_logic = self._find_nearest_logic(segment, logic_formulas)
            
            # Generate explanation
            explanation = requirement_text
            if linked_logic:
                explanation += f" Linked logic: {linked_logic.explanation_nlp}"
            
            # Extract dependency mapping from linked logic
            dependency_mapping: Dict[str, List[str]] = {}
            if linked_logic:
                dependency_mapping = linked_logic.dependency_mapping
            
            requirement = SRSRequirement(
                req_id=req_id,
                page=segment.page,
                requirement_text=requirement_text,
                linked_logic=linked_logic,
                explanation=explanation,
                dependency_mapping=dependency_mapping
            )
            
            requirements.append(requirement)
        
        return requirements
    
    def _find_nearest_logic(self, segment: Segment, logic_formulas: List[LogicFormula]) -> Optional[LogicFormula]:
        """Find nearest logic formula to segment.
        
        Args:
            segment: Segment to find logic for
            logic_formulas: List of logic formulas
            
        Returns:
            Nearest logic formula if found, None otherwise
        """
        # Find logic formulas on same page
        same_page_logic = [lf for lf in logic_formulas if lf.page == segment.page]
        
        if not same_page_logic:
            return None
        
        # Sort by position (use index as proxy since we don't have y coordinates stored in LogicFormula)
        # For now, return first logic on same page (simple heuristic)
        return same_page_logic[0] if same_page_logic else None
    
    def _build_variable_status(self, used_symbols: List[str], glossary: Glossary) -> VariableStatus:
        """Build variable status for equation.
        
        Args:
            used_symbols: List of symbols used in equation
            glossary: Glossary
            
        Returns:
            VariableStatus object
        """
        declared_symbols = []
        initialized_symbols = []
        defined_symbols = []
        missing_declaration = []
        missing_initialization = []
        
        for symbol in used_symbols:
            is_declared = glossary.is_declared(symbol)
            is_initialized = glossary.is_initialized(symbol)
            is_defined = glossary.is_defined(symbol)
            
            if is_declared:
                declared_symbols.append(symbol)
            else:
                missing_declaration.append(symbol)
            
            if is_initialized:
                initialized_symbols.append(symbol)
            else:
                missing_initialization.append(symbol)
            
            if is_defined:  # declared AND initialized
                defined_symbols.append(symbol)
        
        return VariableStatus(
            used_symbols=used_symbols,
            declared_symbols=declared_symbols,
            initialized_symbols=initialized_symbols,
            defined_symbols=defined_symbols,
            missing_declaration=missing_declaration,
            missing_initialization=missing_initialization
        )
    
    def _build_summary(self, equations: List[Equation], logic_formulas: List[LogicFormula],
                      srs_requirements: List[SRSRequirement], glossary: Glossary) -> Summary:
        """Build summary statistics."""
        equations_by_type: Dict[str, int] = {}
        for eq in equations:
            eq_type_str = eq.type.value
            equations_by_type[eq_type_str] = equations_by_type.get(eq_type_str, 0) + 1
        
        logic_by_type: Dict[str, int] = {}
        for logic in logic_formulas:
            logic_type_str = logic.logic_type.value
            logic_by_type[logic_type_str] = logic_by_type.get(logic_type_str, 0) + 1
        
        errors_total = sum(len(eq.errors) for eq in equations)
        errors_total += sum(len(logic.syntax_errors) for logic in logic_formulas)
        
        return Summary(
            equations_total=len(equations),
            logic_total=len(logic_formulas),
            srs_total=len(srs_requirements),
            errors_total=errors_total,
            equations_by_type=equations_by_type,
            logic_by_type=logic_by_type,
            total_declared_symbols=len(glossary.get_declared_symbols()),
            total_initialized_symbols=len(glossary.get_initialized_symbols()),
            total_defined_symbols=len(glossary.get_defined_symbols())
        )
    
    def _collect_errors(self, equations: List[Equation], logic_formulas: List[LogicFormula]) -> List[ErrorReport]:
        """Collect all errors."""
        errors: List[ErrorReport] = []
        for eq in equations:
            errors.extend(eq.errors)
        for logic in logic_formulas:
            errors.extend(logic.syntax_errors)
        return errors
    
    def _generate_doc_id(self, pdf_path: str) -> str:
        """Generate document ID."""
        path_hash = hashlib.md5(pdf_path.encode()).hexdigest()[:8]
        return f"doc-{path_hash}"
    
    def _create_empty_result(self, doc_id: str, file_name: str, pages: int) -> ParseResult:
        """Create empty parse result."""
        return ParseResult(
            doc_id=doc_id,
            file_name=file_name,
            pages=pages,
            summary=Summary(),
            glossary={},
            equations=[],
            logic_formulas=[],
            srs_requirements=[],
            errors=[]
        )
