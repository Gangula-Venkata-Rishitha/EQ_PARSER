"""Glossary extraction: declarations and initializations."""

from typing import Dict, List, Optional, Tuple
import re
from ..models.schema import GlossarySymbol, SourceReference
from ..ingest.pdf_layout import LineMetadata


class Glossary:
    """Glossary engine for tracking symbol declarations and initializations."""
    
    def __init__(self):
        """Initialize glossary."""
        self.symbols: Dict[str, GlossarySymbol] = {}
    
    def extract_from_lines(self, lines: List[LineMetadata]) -> None:
        """Extract declarations and initializations from lines.
        
        Args:
            lines: List of line metadata
        """
        for line in lines:
            # Try to extract declaration
            decl = self._extract_declaration(line)
            if decl:
                symbol, meaning = decl
                self._add_declaration(symbol, meaning, line)
            
            # Try to extract initialization
            init = self._extract_initialization(line)
            if init:
                symbol, value, unit = init
                self._add_initialization(symbol, value, unit, line)
    
    def _extract_declaration(self, line: LineMetadata) -> Optional[Tuple[str, str]]:
        """Extract variable declaration from line.
        
        Pattern: "m = mass", "F = net force", etc.
        RHS should be mostly letters/spaces (no math operators).
        
        Args:
            line: Line metadata
            
        Returns:
            Tuple of (symbol, meaning) if found, None otherwise
        """
        text = line.text.strip()
        
        # Skip if contains math operators (likely equation, not declaration)
        math_ops = ["+", "-", "*", "/", "^", "**", "="]
        if text.count("=") != 1:
            return None
        
        # Pattern: symbol = meaning
        # Also handle bullet points: "• m = mass", "- m = mass", etc.
        patterns = [
            r'^[\s•\u2022\-\*]\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$',  # Bullet prefix
            r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$',  # Direct
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text)
            if match:
                symbol = match.group(1).strip()
                meaning = match.group(2).strip()
                
                # Remove equation label if present (e.g., "(1)")
                meaning = re.sub(r'\s*\([0-9]+\)\s*$', '', meaning)
                
                # Check if RHS is mostly letters/spaces (declaration, not equation)
                # Exclude if contains math operators
                rhs_has_math = any(op in meaning for op in math_ops if op != "=")
                if rhs_has_math:
                    continue
                
                # Check if RHS looks like text (mostly letters)
                letter_count = sum(1 for c in meaning if c.isalpha() or c.isspace())
                total_non_space = len(meaning.replace(" ", ""))
                
                if total_non_space > 0 and letter_count / total_non_space > 0.6:
                    return (symbol, meaning)
        
        return None
    
    def _extract_initialization(self, line: LineMetadata) -> Optional[Tuple[str, float, Optional[str]]]:
        """Extract variable initialization from line.
        
        Pattern: "m = 5", "a=10", "g = 9.81 m/s^2"
        
        Args:
            line: Line metadata
            
        Returns:
            Tuple of (symbol, value, unit) if found, None otherwise
        """
        text = line.text.strip()
        
        # Must contain exactly one "="
        if text.count("=") != 1:
            return None
        
        # Pattern: symbol = number [unit]
        patterns = [
            r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([0-9]+\.?[0-9]*)\s*(.*)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text)
            if match:
                symbol = match.group(1).strip()
                value_str = match.group(2).strip()
                unit_str = match.group(3).strip() if match.group(3) else None
                
                try:
                    value = float(value_str)
                    
                    # Clean unit string (remove extra whitespace, preserve structure)
                    unit = None
                    if unit_str:
                        unit = unit_str.strip()
                        if not unit:  # Empty after strip
                            unit = None
                    
                    return (symbol, value, unit)
                except ValueError:
                    continue
        
        return None
    
    def _add_declaration(self, symbol: str, meaning: str, line: LineMetadata) -> None:
        """Add declaration for symbol.
        
        Args:
            symbol: Symbol name
            meaning: Meaning/description
            line: Source line
        """
        if symbol not in self.symbols:
            self.symbols[symbol] = GlossarySymbol(
                meaning=meaning,
                declared=False,
                initialized=False,
                defined=False
            )
        
        sym = self.symbols[symbol]
        sym.meaning = meaning
        sym.declared = True
        sym.sources.append(SourceReference(
            page=line.page,
            raw=line.text,
            type="declaration"
        ))
        
        # Update defined status
        sym.defined = sym.declared and sym.initialized
    
    def _add_initialization(self, symbol: str, value: float, unit: Optional[str], line: LineMetadata) -> None:
        """Add initialization for symbol.
        
        Args:
            symbol: Symbol name
            value: Numeric value
            unit: Unit (optional)
            line: Source line
        """
        if symbol not in self.symbols:
            self.symbols[symbol] = GlossarySymbol(
                declared=False,
                initialized=False,
                defined=False
            )
        
        sym = self.symbols[symbol]
        sym.initialized = True
        
        # Add value
        if value not in sym.values:
            sym.values.append(value)
        
        # Update unit if not set or if this is more informative
        if unit and (not sym.unit or len(unit) > len(sym.unit or "")):
            sym.unit = unit
        
        sym.sources.append(SourceReference(
            page=line.page,
            raw=line.text,
            type="initialization"
        ))
        
        # Update defined status
        sym.defined = sym.declared and sym.initialized
    
    def get_symbol(self, symbol: str) -> Optional[GlossarySymbol]:
        """Get glossary entry for symbol.
        
        Args:
            symbol: Symbol name
            
        Returns:
            Glossary symbol if found, None otherwise
        """
        return self.symbols.get(symbol)
    
    def is_declared(self, symbol: str) -> bool:
        """Check if symbol is declared.
        
        Args:
            symbol: Symbol name
            
        Returns:
            True if declared
        """
        return symbol in self.symbols and self.symbols[symbol].declared
    
    def is_initialized(self, symbol: str) -> bool:
        """Check if symbol is initialized.
        
        Args:
            symbol: Symbol name
            
        Returns:
            True if initialized
        """
        return symbol in self.symbols and self.symbols[symbol].initialized
    
    def is_defined(self, symbol: str) -> bool:
        """Check if symbol is defined (declared AND initialized).
        
        Args:
            symbol: Symbol name
            
        Returns:
            True if defined
        """
        return symbol in self.symbols and self.symbols[symbol].defined
    
    def get_declared_symbols(self) -> List[str]:
        """Get list of all declared symbols.
        
        Returns:
            List of symbol names
        """
        return [s for s, sym in self.symbols.items() if sym.declared]
    
    def get_initialized_symbols(self) -> List[str]:
        """Get list of all initialized symbols.
        
        Returns:
            List of symbol names
        """
        return [s for s, sym in self.symbols.items() if sym.initialized]
    
    def get_defined_symbols(self) -> List[str]:
        """Get list of all defined symbols (declared AND initialized).
        
        Returns:
            List of symbol names
        """
        return [s for s, sym in self.symbols.items() if sym.defined]
    
    def to_dict(self) -> Dict[str, GlossarySymbol]:
        """Convert glossary to dictionary.
        
        Returns:
            Dictionary of symbol -> GlossarySymbol
        """
        return self.symbols.copy()
