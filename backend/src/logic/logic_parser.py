"""Logic formula parser: classification, validation, form detection."""

from typing import List, Dict, Tuple, Optional
import re
from ..models.schema import LogicType, LogicForm, ErrorReport, ErrorType


# LTL operators
LTL_OPERATORS = {
    "G": "globally", "F": "eventually", "X": "next",
    "U": "until", "R": "release"
}

# CTL operators
CTL_OPERATORS = {
    "AX": "all next", "EX": "exists next",
    "AF": "all eventually", "EF": "exists eventually",
    "AG": "all globally", "EG": "exists globally",
    "AU": "all until", "EU": "exists until",
    "A": "all paths", "E": "exists path"
}

# Boolean operators
BOOLEAN_OPERATORS = {
    "and": "∧", "or": "∨", "not": "¬", "implies": "→", "iff": "↔",
    "∧": "∧", "∨": "∨", "¬": "¬", "→": "→", "↔": "↔",
    "&": "∧", "|": "∨", "!": "¬", "->": "→", "<->": "↔"
}

# Quantifiers
QUANTIFIERS = {"∀": "for all", "∃": "exists", "forall": "∀", "exists": "∃"}


class LogicFormulaParser:
    """Parser for logic formulas."""
    
    def parse(self, formula: str) -> Dict:
        """Parse logic formula and return structured data.
        
        Args:
            formula: Logic formula string
            
        Returns:
            Dictionary with:
            - raw: original formula
            - normalized: normalized formula
            - logic_type: LogicType
            - form: LogicForm
            - is_valid: bool
            - syntax_errors: List[ErrorReport]
            - dependency_mapping: Dict
        """
        raw = formula.strip()
        normalized = self._normalize_formula(raw)
        
        # Detect form
        form = self._detect_form(raw)
        
        # Classify type
        logic_type = self._classify_type(normalized)
        
        # Validate
        is_valid, syntax_errors = self._validate_formula(normalized, logic_type)
        
        # Extract dependency mapping
        dependency_mapping = self._extract_dependency_mapping(normalized, logic_type)
        
        return {
            "raw": raw,
            "normalized": normalized,
            "logic_type": logic_type,
            "form": form,
            "is_valid": is_valid,
            "syntax_errors": syntax_errors,
            "dependency_mapping": dependency_mapping
        }
    
    def _normalize_formula(self, formula: str) -> str:
        """Normalize formula string.
        
        Args:
            formula: Raw formula string
            
        Returns:
            Normalized formula
        """
        normalized = formula
        
        # Normalize boolean operators
        for word, symbol in BOOLEAN_OPERATORS.items():
            if word != symbol:
                # Replace whole word (with word boundaries)
                pattern = r'\b' + re.escape(word) + r'\b'
                normalized = re.sub(pattern, symbol, normalized, flags=re.IGNORECASE)
        
        # Normalize quantifiers
        for word, symbol in QUANTIFIERS.items():
            if word != symbol:
                pattern = r'\b' + re.escape(word) + r'\b'
                normalized = re.sub(pattern, symbol, normalized, flags=re.IGNORECASE)
        
        # Normalize spacing
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.strip()
        
        return normalized
    
    def _detect_form(self, formula: str) -> LogicForm:
        """Detect formula form (infix/prefix/postfix).
        
        Args:
            formula: Formula string
            
        Returns:
            LogicForm
        """
        # Prefix: operators before operands (e.g., "AND P Q")
        prefix_patterns = [r'^(G|F|X|U|R|AX|EX|AF|EF|AG|EG|AU|EU|∀|∃|¬)\s+']
        if any(re.match(pattern, formula, re.IGNORECASE) for pattern in prefix_patterns):
            return LogicForm.PREFIX
        
        # Postfix: operators after operands (e.g., "P Q AND")
        # Check if ends with operator
        postfix_patterns = [r'\s+(AND|OR|U|R)$', r'([PQ][PQ].*[AND|OR])$']
        if any(re.search(pattern, formula, re.IGNORECASE) for pattern in postfix_patterns):
            return LogicForm.POSTFIX
        
        # Default: infix (e.g., "P AND Q", "P ∧ Q")
        return LogicForm.INFIX
    
    def _classify_type(self, formula: str) -> LogicType:
        """Classify logic formula type.
        
        Args:
            formula: Normalized formula string
            
        Returns:
            LogicType
        """
        formula_upper = formula.upper()
        
        # Check for CTL operators
        ctl_ops = ["AX", "EX", "AF", "EF", "AG", "EG", "AU", "EU"]
        if any(op in formula_upper for op in ctl_ops):
            # Also check for A[...] or E[...] patterns
            if re.search(r'A\s*\[|E\s*\[', formula_upper):
                return LogicType.CTL
            return LogicType.CTL
        
        # Check for LTL operators
        ltl_ops = ["G", "F", "X", "U", "R"]
        if any(op in formula for op in ltl_ops):
            # Must be standalone (not part of CTL)
            if not any(op in formula_upper for op in ["AX", "EX", "AF", "EF"]):
                return LogicType.LTL
        
        # Check for quantifiers (predicate logic)
        if any(q in formula for q in ["∀", "∃", "FORALL", "EXISTS"]):
            return LogicType.PREDICATE
        
        # Default: propositional
        return LogicType.PROPOSITIONAL
    
    def _validate_formula(self, formula: str, logic_type: LogicType) -> Tuple[bool, List[ErrorReport]]:
        """Validate formula syntax.
        
        Args:
            formula: Normalized formula string
            logic_type: Logic type
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors: List[ErrorReport] = []
        
        # Check bracket matching
        bracket_errors = self._check_brackets(formula)
        errors.extend(bracket_errors)
        
        # Check operator arity
        arity_errors = self._check_operator_arity(formula, logic_type)
        errors.extend(arity_errors)
        
        # Check CTL until format if CTL
        if logic_type == LogicType.CTL:
            ctl_errors = self._check_ctl_format(formula)
            errors.extend(ctl_errors)
        
        # Check dangling operators
        dangling_errors = self._check_dangling_operators(formula)
        errors.extend(dangling_errors)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _check_brackets(self, formula: str) -> List[ErrorReport]:
        """Check bracket matching.
        
        Args:
            formula: Formula string
            
        Returns:
            List of bracket errors
        """
        errors: List[ErrorReport] = []
        bracket_pairs = {"(": ")", "[": "]", "{": "}"}
        stack = []
        
        for i, char in enumerate(formula):
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
                            message=f"Mismatched brackets: '{opening}' expects '{expected_closing}'",
                            location=f"position {i}"
                        ))
        
        if stack:
            for opening, expected_closing, pos in stack:
                errors.append(ErrorReport(
                    error_type=ErrorType.MISSING_BRACKETS,
                    message=f"Unclosed bracket '{opening}'",
                    location=f"position {pos}"
                ))
        
        return errors
    
    def _check_operator_arity(self, formula: str, logic_type: LogicType) -> List[ErrorReport]:
        """Check operator arity.
        
        Args:
            formula: Formula string
            logic_type: Logic type
            
        Returns:
            List of arity errors
        """
        errors: List[ErrorReport] = []
        # Basic check - operators should have appropriate operands
        # This is simplified; full arity checking is complex
        return errors
    
    def _check_ctl_format(self, formula: str) -> List[ErrorReport]:
        """Check CTL until format (e.g., A[p U q]).
        
        Args:
            formula: Formula string
            
        Returns:
            List of CTL format errors
        """
        errors: List[ErrorReport] = []
        # Check A[...] and E[...] patterns
        ctl_pattern = r'(A|E)\s*\[([^\]]+)\s+U\s+([^\]]+)\]'
        matches = list(re.finditer(ctl_pattern, formula))
        
        if "U" in formula or "EU" in formula or "AU" in formula:
            # Basic validation - check if brackets are balanced
            if "[" in formula:
                if not re.search(ctl_pattern, formula):
                    errors.append(ErrorReport(
                        error_type=ErrorType.SYNTAX_ERROR,
                        message="CTL until format should be A[p U q] or E[p U q]",
                        location="formula"
                    ))
        
        return errors
    
    def _check_dangling_operators(self, formula: str) -> List[ErrorReport]:
        """Check for dangling operators.
        
        Args:
            formula: Formula string
            
        Returns:
            List of dangling operator errors
        """
        errors: List[ErrorReport] = []
        
        formula_stripped = formula.strip()
        if not formula_stripped:
            return errors
        
        # Check if formula ends with binary operator
        binary_ops = ["∧", "∨", "→", "↔", "U", "R", "&", "|", "->", "<->", "AND", "OR"]
        for op in binary_ops:
            if formula_stripped.endswith(op):
                errors.append(ErrorReport(
                    error_type=ErrorType.DANGLING_OPERATOR,
                    message=f"Formula ends with operator '{op}'",
                    location="end of formula"
                ))
        
        return errors
    
    def _extract_dependency_mapping(self, formula: str, logic_type: LogicType) -> Dict[str, List[str]]:
        """Extract dependency mapping (atoms, operators, etc.).
        
        Args:
            formula: Normalized formula string
            logic_type: Logic type
            
        Returns:
            Dictionary with dependency mappings
        """
        mapping: Dict[str, List[str]] = {
            "atoms": [],
            "boolean_operators": [],
            "temporal_operators": [],
            "path_operators": [],
            "quantifiers": []
        }
        
        # Extract atoms (propositional variables)
        atoms = re.findall(r'\b[A-Z][a-z0-9]*\b', formula)
        mapping["atoms"] = sorted(list(set(atoms)))
        
        # Extract boolean operators
        for op in BOOLEAN_OPERATORS.values():
            if op in formula:
                mapping["boolean_operators"].append(op)
        
        # Extract temporal operators (LTL)
        if logic_type == LogicType.LTL:
            for op in LTL_OPERATORS:
                if op in formula:
                    mapping["temporal_operators"].append(op)
        
        # Extract path operators (CTL)
        if logic_type == LogicType.CTL:
            for op in ["AX", "EX", "AF", "EF", "AG", "EG", "AU", "EU"]:
                if op in formula:
                    mapping["path_operators"].append(op)
            if "A" in formula:
                mapping["path_operators"].append("A")
            if "E" in formula:
                mapping["path_operators"].append("E")
        
        # Extract quantifiers
        for q in QUANTIFIERS.values():
            if q in formula:
                mapping["quantifiers"].append(q)
        
        return mapping
