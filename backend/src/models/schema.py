"""Pydantic models for JSON schema validation and serialization."""

from typing import Dict, List, Optional, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum


class ErrorType(str, Enum):
    """Equation error types."""
    MISSING_BRACKETS = "missing_brackets"
    DANGLING_OPERATOR = "dangling_operator"
    MISSING_OPERAND = "missing_operand"
    MALFORMED_EQUALS = "malformed_equals"
    SUSPICIOUS_EXPONENT = "suspicious_exponent"
    INCOMPLETE_FRACTION = "incomplete_fraction"
    INCOMPLETE_PARENTHESIS = "incomplete_parenthesis"
    SYNTAX_ERROR = "syntax_error"


class EquationType(str, Enum):
    """Equation classification types."""
    FORCES = "forces"
    KINEMATICS = "kinematics"
    ENERGY_WORK = "energy_work"
    MOMENTUM = "momentum"
    SUMMATION = "summation"
    CALCULUS = "calculus"
    LINEAR_ALGEBRA = "linear_algebra"
    GENERIC_ALGEBRA = "generic_algebra"
    UNKNOWN = "unknown"


class LogicType(str, Enum):
    """Logic formula types."""
    PROPOSITIONAL = "propositional"
    PREDICATE = "predicate"
    LTL = "ltl"
    CTL = "ctl"


class LogicForm(str, Enum):
    """Logic formula forms."""
    INFIX = "infix"
    PREFIX = "prefix"
    POSTFIX = "postfix"


class ErrorReport(BaseModel):
    """Individual error report."""
    error_type: ErrorType
    message: str
    location: Optional[str] = None


class SourceReference(BaseModel):
    """Source reference for glossary entries."""
    page: int
    raw: str
    type: Literal["declaration", "initialization"]


class GlossarySymbol(BaseModel):
    """Glossary entry for a symbol."""
    meaning: Optional[str] = None
    unit: Optional[str] = None
    declared: bool = False
    initialized: bool = False
    defined: bool = False  # declared AND initialized
    values: List[Union[float, str]] = Field(default_factory=list)
    sources: List[SourceReference] = Field(default_factory=list)


class VariableStatus(BaseModel):
    """Variable status for an equation."""
    used_symbols: List[str] = Field(default_factory=list)
    declared_symbols: List[str] = Field(default_factory=list)
    initialized_symbols: List[str] = Field(default_factory=list)
    defined_symbols: List[str] = Field(default_factory=list)
    missing_declaration: List[str] = Field(default_factory=list)
    missing_initialization: List[str] = Field(default_factory=list)


class Equation(BaseModel):
    """Extracted equation."""
    eq_id: str
    page: int
    label: Optional[str] = None
    raw: str
    normalized: str
    type: EquationType
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation_nlp: str
    variables: VariableStatus
    errors: List[ErrorReport] = Field(default_factory=list)


class LogicFormula(BaseModel):
    """Extracted logic formula."""
    formula_id: str
    page: int
    raw: str
    normalized: str
    logic_type: LogicType
    form: LogicForm
    is_valid: bool
    syntax_errors: List[ErrorReport] = Field(default_factory=list)
    explanation_nlp: str
    dependency_mapping: Dict[str, List[str]] = Field(default_factory=dict)


class SRSRequirement(BaseModel):
    """Extracted SRS requirement."""
    req_id: str
    page: int
    requirement_text: str
    linked_logic: Optional[LogicFormula] = None
    explanation: str
    dependency_mapping: Dict[str, List[str]] = Field(default_factory=dict)


class Summary(BaseModel):
    """Summary statistics."""
    equations_total: int = 0
    logic_total: int = 0
    srs_total: int = 0
    errors_total: int = 0
    equations_by_type: Dict[str, int] = Field(default_factory=dict)
    logic_by_type: Dict[str, int] = Field(default_factory=dict)
    total_declared_symbols: int = 0
    total_initialized_symbols: int = 0
    total_defined_symbols: int = 0


class ParseResult(BaseModel):
    """Complete parse result."""
    doc_id: str
    file_name: str
    pages: int
    summary: Summary
    glossary: Dict[str, GlossarySymbol] = Field(default_factory=dict)
    equations: List[Equation] = Field(default_factory=list)
    logic_formulas: List[LogicFormula] = Field(default_factory=list)
    srs_requirements: List[SRSRequirement] = Field(default_factory=list)
    errors: List[ErrorReport] = Field(default_factory=list)


class ConvertEquationToNLPRequest(BaseModel):
    """Request for equation to NLP conversion."""
    equation: str


class ConvertEquationToNLPResponse(BaseModel):
    """Response for equation to NLP conversion."""
    equation: str
    nlp: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ConvertNLPToEquationRequest(BaseModel):
    """Request for NLP to equation conversion."""
    nlp: str
    doc_id: Optional[str] = None  # If provided, use glossary from doc


class ConvertNLPToEquationResponse(BaseModel):
    """Response for NLP to equation conversion."""
    nlp: str
    candidates: List[Dict[str, Union[str, float]]] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Chatbot request."""
    doc_id: str
    message: str


class ChatResponse(BaseModel):
    """Chatbot response."""
    message: str
    response: str
    references: List[Dict[str, str]] = Field(default_factory=list)
