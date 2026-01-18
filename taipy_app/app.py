"""Taipy test UI for equation parser backend.
Note: May have compatibility issues with Python 3.13.
Use app_simple.py as fallback if this fails.
"""

try:
    from taipy import Gui
    TAIPY_AVAILABLE = True
except ImportError:
    TAIPY_AVAILABLE = False
    print("Warning: Taipy not available. Use app_simple.py instead.")

import requests
import os

# Backend API URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

if not TAIPY_AVAILABLE:
    print("Taipy is not available. Please install it or use app_simple.py")
    exit(1)

# UI components
upload_page = """
<|layout|columns=1 2|
<|part|partial={upload_section}|>

<|part|partial={results_section}|>
|>
"""

def upload_section(state):
    return """
<|card|
## Upload PDF
<|{pdf_file}|file_selector|label=Select PDF|extensions=.pdf|on_action=on_file_selected|>
<|{parse_status}|text|label=Status|>
<|Parse|button|on_action=parse_pdf|active={len(pdf_file)>0}|>
|>
"""

def results_section(state):
    if not state.get("parse_result"):
        return """
<|card|
## Results
Upload a PDF to see results.
|>
"""
    
    result = state.parse_result
    summary = result.get("summary", {})
    
    return f"""
<|card|
## Summary
- Equations: {summary.get('equations_total', 0)}
- Logic Formulas: {summary.get('logic_total', 0)}
- SRS Requirements: {summary.get('srs_total', 0)}
- Errors: {summary.get('errors_total', 0)}
|>

<|card|
## Equations
<|{get_equations_text(state)}|text|>
|>

<|card|
## Errors
<|{get_errors_text(state)}|text|>
|>
"""

def get_equations_text(state):
    result = state.get("parse_result", {})
    equations = result.get("equations", [])
    if not equations:
        return "No equations found."
    
    text_parts = []
    for eq in equations[:10]:  # Show first 10
        eq_id = eq.get("eq_id", "")
        raw = eq.get("raw", "")
        errors = eq.get("errors", [])
        error_count = len(errors)
        text_parts.append(f"{eq_id}: {raw} ({error_count} errors)")
    
    return "\n".join(text_parts)

def get_errors_text(state):
    result = state.get("parse_result", {})
    all_errors = result.get("errors", [])
    if not all_errors:
        return "No errors found."
    
    text_parts = []
    for err in all_errors[:20]:  # Show first 20
        error_type = err.get("error_type", "")
        message = err.get("message", "")
        text_parts.append(f"{error_type}: {message}")
    
    return "\n".join(text_parts)

# State variables
pdf_file = ""
parse_status = "Ready"
parse_result = None

def on_file_selected(state):
    state.pdf_file = state.pdf_file if state.pdf_file else ""

def parse_pdf(state):
    if not state.pdf_file:
        state.parse_status = "No file selected"
        return
    
    state.parse_status = "Parsing..."
    
    try:
        # Read file
        with open(state.pdf_file, "rb") as f:
            files = {"file": (os.path.basename(state.pdf_file), f, "application/pdf")}
            response = requests.post(f"{API_BASE_URL}/parse", files=files)
        
        if response.status_code == 200:
            state.parse_result = response.json()
            state.parse_status = "Success"
        else:
            state.parse_status = f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        state.parse_status = f"Error: {str(e)}"

# Create GUI
try:
    gui = Gui(page=upload_page)
    gui.add_partial("upload_section", upload_section)
    gui.add_partial("results_section", results_section)

    if __name__ == "__main__":
        gui.run(port=5000, debug=True)
except Exception as e:
    print(f"Error starting Taipy GUI: {e}")
    print("Note: Taipy has known compatibility issues with Python 3.13.")
    print("Please use app_simple.py as an alternative or use the npm frontend.")
    exit(1)
