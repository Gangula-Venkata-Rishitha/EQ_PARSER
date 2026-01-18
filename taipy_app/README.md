# Taipy Test UI

Optional test UI for the equation parser backend. **Note**: Taipy has known compatibility issues with Python 3.13 due to SQLAlchemy conflicts.

## Installation

```bash
pip install taipy requests
```

## Usage

### Option 1: Taipy GUI (if compatible)
```bash
python app.py
```

### Option 2: Simple CLI Test Interface (recommended if Taipy fails)
```bash
python app_simple.py
```

The simple CLI interface provides basic functionality without Taipy dependencies.

## Alternative: Use npm Frontend

For the best experience, use the npm frontend instead:
```bash
cd ../frontend
npm install
npm run dev
```
