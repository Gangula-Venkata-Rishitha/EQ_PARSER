"""Equation classification: rules-first approach."""

from typing import Dict, Tuple
from ..models.schema import EquationType
import re


# Feature sets for classification
FORCE_SYMBOLS = {"F", "f", "force", "net_force", "ΣF", "sum_F"}
KINEMATICS_SYMBOLS = {"v", "velocity", "a", "acceleration", "s", "distance", "t", "time", "u", "u0"}
ENERGY_SYMBOLS = {"E", "energy", "K", "kinetic", "U", "potential", "W", "work"}
MOMENTUM_SYMBOLS = {"p", "momentum", "m", "mass"}
CALCULUS_OPERATORS = {"∂", "d/", "d/d", "integral", "∫", "sum_", "Σ", "∑"}
LINEAR_ALGEBRA_PATTERNS = {"matrix", "vector", "dot", "cross", "×"}


def classify_equation(equation: str, symbols: list) -> Tuple[EquationType, float]:
    """Classify equation type using rules-first approach.
    
    Args:
        equation: Equation string (normalized)
        symbols: List of symbols in equation
        
    Returns:
        Tuple of (equation_type, confidence_score)
    """
    equation_lower = equation.lower()
    symbol_set = {s.lower() for s in symbols}
    
    scores: Dict[EquationType, float] = {
        EquationType.FORCES: 0.0,
        EquationType.KINEMATICS: 0.0,
        EquationType.ENERGY_WORK: 0.0,
        EquationType.MOMENTUM: 0.0,
        EquationType.SUMMATION: 0.0,
        EquationType.CALCULUS: 0.0,
        EquationType.LINEAR_ALGEBRA: 0.0,
        EquationType.GENERIC_ALGEBRA: 0.0,
        EquationType.UNKNOWN: 0.0,
    }
    
    # Check for summation operators
    if any(op in equation for op in ["sum_", "Σ", "∑"]):
        scores[EquationType.SUMMATION] += 0.5
        scores[EquationType.FORCES] += 0.2  # Often used with forces
    
    # Check for calculus operators
    if any(op in equation for op in ["∂", "d/", "integral", "∫"]):
        scores[EquationType.CALCULUS] += 0.8
    
    # Check force symbols
    force_matches = symbol_set.intersection(FORCE_SYMBOLS)
    if force_matches:
        scores[EquationType.FORCES] += 0.6
        # Common: F = m*a
        if "m" in symbol_set and "a" in symbol_set:
            scores[EquationType.FORCES] += 0.3
    
    # Check kinematics symbols
    kin_matches = symbol_set.intersection(KINEMATICS_SYMBOLS)
    if kin_matches:
        scores[EquationType.KINEMATICS] += 0.5
        # Common patterns
        if "v" in symbol_set and "a" in symbol_set and "t" in symbol_set:
            scores[EquationType.KINEMATICS] += 0.3
        if "s" in symbol_set and "t" in symbol_set:
            scores[EquationType.KINEMATICS] += 0.2
    
    # Check energy/work symbols
    energy_matches = symbol_set.intersection(ENERGY_SYMBOLS)
    if energy_matches:
        scores[EquationType.ENERGY_WORK] += 0.6
        # Common: K = 1/2*m*v^2
        if any(k in symbol_set for k in ["k", "kinetic"]) and "m" in symbol_set and "v" in symbol_set:
            scores[EquationType.ENERGY_WORK] += 0.3
    
    # Check momentum symbols
    momentum_matches = symbol_set.intersection(MOMENTUM_SYMBOLS)
    if momentum_matches and "p" in symbol_set:
        scores[EquationType.MOMENTUM] += 0.6
        if "m" in symbol_set and "v" in symbol_set:
            scores[EquationType.MOMENTUM] += 0.3
    
    # Check linear algebra patterns
    if any(pattern in equation_lower for pattern in LINEAR_ALGEBRA_PATTERNS):
        scores[EquationType.LINEAR_ALGEBRA] += 0.5
    
    # Find max score
    max_type = max(scores.items(), key=lambda x: x[1])
    
    if max_type[1] > 0.3:
        eq_type = max_type[0]
        confidence = min(max_type[1], 1.0)
    else:
        # Low confidence -> generic or unknown
        if len(symbols) > 0:
            eq_type = EquationType.GENERIC_ALGEBRA
            confidence = 0.3
        else:
            eq_type = EquationType.UNKNOWN
            confidence = 0.1
    
    return eq_type, confidence
