# Equation Parser Backend

Production-ready PDF equation parser backend built with FastAPI.

## Features

- **PDF Parsing**: Layout-aware extraction of equations, logic formulas, and SRS requirements from IEEE papers
- **Equation Validation**: Explicit error flagging (never silently skips malformed equations)
- **Glossary Engine**: Tracks variable declarations, initializations, and definitions
- **Equation Classification**: Rules-first classifier for equation types
- **Logic Parsing**: Support for Propositional, Predicate, LTL, and CTL logic
- **SRS Extraction**: Requirement extraction with tight heuristics
- **Equation ↔ NLP**: Bidirectional conversion between equations and natural language
- **Chatbot**: Mini chatbot for querying parsed documents

## Setup

### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Run Backend Server

```bash
# Using Python module (recommended on Windows)
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or if uvicorn is in PATH
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Parse PDF
```bash
curl -X POST "http://localhost:8000/parse" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@example.pdf"
```

### Get Document Summary
```bash
curl "http://localhost:8000/document/{doc_id}/summary"
```

### Get Equations
```bash
curl "http://localhost:8000/document/{doc_id}/equations"
```

### Get Logic Formulas
```bash
curl "http://localhost:8000/document/{doc_id}/logic"
```

### Get SRS Requirements
```bash
curl "http://localhost:8000/document/{doc_id}/srs"
```

### Convert Equation to NLP
```bash
curl -X POST "http://localhost:8000/convert/equation-to-nlp" \
  -H "Content-Type: application/json" \
  -d '{"equation": "F = m * a"}'
```

### Convert NLP to Equation
```bash
curl -X POST "http://localhost:8000/convert/nlp-to-equation" \
  -H "Content-Type: application/json" \
  -d '{"nlp": "net force equals mass times acceleration"}'
```

### Chat
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "doc-12345", "message": "Explain equation eq-0001"}'
```

## Architecture

- `/src/ingest/`: PDF extraction and filtering
- `/src/glossary/`: Variable declaration/initialization tracking
- `/src/math/`: Equation processing (validation, classification, NLP)
- `/src/logic/`: Logic formula parsing and translation
- `/src/srs/`: SRS requirement extraction
- `/src/api/`: FastAPI routes and main app
- `/src/storage/`: Artifact storage (JSON files)
- `/src/models/`: Pydantic models for JSON schema

## Development

Run tests:
```bash
pytest backend/tests/
```

## Notes

- Artifacts are stored in `artifacts/` directory
- The system NEVER silently skips equations with errors
- Dependency graphs are NOT generated (only dependency mapping)
- Variable status: `defined = declared AND initialized`
