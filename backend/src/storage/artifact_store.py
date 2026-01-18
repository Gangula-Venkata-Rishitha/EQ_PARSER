"""Artifact storage for parsed documents."""

import json
import os
from pathlib import Path
from typing import Optional
from ..models.schema import ParseResult


class ArtifactStore:
    """Store and retrieve parsed document artifacts."""
    
    def __init__(self, storage_dir: str = "artifacts"):
        """Initialize artifact store.
        
        Args:
            storage_dir: Directory to store artifacts (relative to project root)
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, doc_id: str, result: ParseResult) -> None:
        """Save parse result to disk.
        
        Args:
            doc_id: Document identifier
            result: Parse result to save
        """
        file_path = self.storage_dir / f"{doc_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
    
    def load(self, doc_id: str) -> Optional[ParseResult]:
        """Load parse result from disk.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Parse result if found, None otherwise
        """
        file_path = self.storage_dir / f"{doc_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return ParseResult(**data)
    
    def exists(self, doc_id: str) -> bool:
        """Check if document exists in storage.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            True if document exists, False otherwise
        """
        file_path = self.storage_dir / f"{doc_id}.json"
        return file_path.exists()
