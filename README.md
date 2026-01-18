# Equation Parser - Production-Ready PDF Equation Extractor

A complete web application that parses research PDFs (including IEEE papers) and extracts:
- Equations (with validation, classification, and NLP explanations)
- Variable declarations/initializations/definitions
- Logic formulas (LTL/CTL/Predicate/Propositional)
- SRS requirements
- Dependency mapping
- Error reports

## Features

- ✅ **Layout-aware PDF extraction** (IEEE-robust)
- ✅ **Explicit error flagging** (never silently skips malformed equations)
- ✅ **Glossary engine** (declared/initialized/defined variable tracking)
- ✅ **Equation ↔ NLP conversion**
- ✅ **Mini chatbot** for querying extracted data
- ✅ **FastAPI backend** + **npm frontend** + **Taipy test UI**

## Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn src.api.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Taipy Test UI (Development) - Optional

**Note**: Taipy has known compatibility issues with Python 3.13. Use the simple CLI test interface instead if Taipy fails.

```bash
cd taipy_app
pip install taipy requests
python app.py          # May fail on Python 3.13
python app_simple.py   # Fallback simple CLI interface
```

## Architecture

```
backend/
  src/
    ingest/        # PDF extraction (layout-aware, filtering)
    glossary/      # Variable declarations/initializations
    math/          # Equation processing (validation, classification, NLP)
    logic/         # Logic formula parsing
    srs/           # SRS requirement extraction
    api/           # FastAPI routes
    storage/       # Artifact storage
    models/        # Pydantic schemas

frontend/
  src/             # React/Next.js frontend (minimalistic UI)

taipy_app/
  app.py           # Taipy test UI for development
```

## Hard Constraints (Enforced)

1. **Only outputs relevant data**: No titles, headings, paragraphs, abstracts, references
2. **Explicit error flagging**: Equations with errors are flagged, not silently skipped
3. **No dependency graphs**: Only dependency mapping (structured data)
4. **Variable status rule**: `defined = declared AND initialized` (strict)
5. **Equation ↔ NLP conversion**: Bidirectional conversion supported

## API Examples

See `backend/README.md` for detailed API documentation.

## Development

The system follows strict requirements:
- Equations are validated before parsing (explicit errors)
- Glossary tracks declared/initialized/defined separately
- Logic formulas are classified (LTL/CTL/Predicate/Propositional)
- SRS extraction uses tight heuristics to avoid false positives
- All outputs follow strict JSON schema

## License

MIT
