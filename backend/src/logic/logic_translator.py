"""Logic formula translation to natural language."""

from typing import Dict, Optional
from .logic_parser import LogicFormulaParser
from ..models.schema import LogicFormula


def explain_logic_formula(formula_data: Dict) -> str:
    """Explain logic formula in natural language.
    
    Args:
        formula_data: Parsed formula data (from LogicFormulaParser)
        
    Returns:
        Natural language explanation
    """
    logic_type = formula_data["logic_type"]
    normalized = formula_data["normalized"]
    dependency_mapping = formula_data.get("dependency_mapping", {})
    
    explanation_parts = []
    
    # Type description
    type_descriptions = {
        "propositional": "propositional logic formula",
        "predicate": "predicate logic formula",
        "ltl": "linear temporal logic (LTL) formula",
        "ctl": "computation tree logic (CTL) formula"
    }
    type_desc = type_descriptions.get(logic_type.value.lower(), "logic formula")
    explanation_parts.append(f"This is a {type_desc}.")
    
    # Operator explanation
    atoms = dependency_mapping.get("atoms", [])
    if atoms:
        explanation_parts.append(f"Atomic propositions: {', '.join(atoms)}.")
    
    boolean_ops = dependency_mapping.get("boolean_operators", [])
    if boolean_ops:
        op_descriptions = {
            "∧": "conjunction (AND)",
            "∨": "disjunction (OR)",
            "¬": "negation (NOT)",
            "→": "implication",
            "↔": "biconditional (iff)"
        }
        op_desc_list = [op_descriptions.get(op, op) for op in boolean_ops]
        explanation_parts.append(f"Boolean operators: {', '.join(op_desc_list)}.")
    
    # Temporal operators (LTL)
    if logic_type.value == "ltl":
        temporal_ops = dependency_mapping.get("temporal_operators", [])
        if temporal_ops:
            ltl_descriptions = {
                "G": "globally (always)",
                "F": "eventually",
                "X": "next",
                "U": "until",
                "R": "release"
            }
            temporal_desc_list = [ltl_descriptions.get(op, op) for op in temporal_ops]
            explanation_parts.append(f"Temporal operators: {', '.join(temporal_desc_list)}.")
    
    # Path operators (CTL)
    if logic_type.value == "ctl":
        path_ops = dependency_mapping.get("path_operators", [])
        if path_ops:
            ctl_descriptions = {
                "AX": "all paths next",
                "EX": "exists path next",
                "AF": "all paths eventually",
                "EF": "exists path eventually",
                "AG": "all paths globally",
                "EG": "exists path globally",
                "AU": "all paths until",
                "EU": "exists path until"
            }
            path_desc_list = [ctl_descriptions.get(op, op) for op in path_ops]
            explanation_parts.append(f"Path operators: {', '.join(path_desc_list)}.")
    
    # Quantifiers (predicate)
    if logic_type.value == "predicate":
        quantifiers = dependency_mapping.get("quantifiers", [])
        if quantifiers:
            quant_descriptions = {
                "∀": "for all",
                "∃": "exists"
            }
            quant_desc_list = [quant_descriptions.get(q, q) for q in quantifiers]
            explanation_parts.append(f"Quantifiers: {', '.join(quant_desc_list)}.")
    
    # Validity
    is_valid = formula_data.get("is_valid", False)
    if is_valid:
        explanation_parts.append("The formula is syntactically valid.")
    else:
        explanation_parts.append("The formula has syntax errors.")
    
    return " ".join(explanation_parts)
