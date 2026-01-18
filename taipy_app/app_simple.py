"""Simple test UI for equation parser backend (alternative to Taipy)."""

import requests
import os
import json

# Backend API URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def main():
    """Simple CLI test interface."""
    print("=" * 60)
    print("Equation Parser - Test Interface")
    print("=" * 60)
    print(f"Backend URL: {API_BASE_URL}")
    print()
    
    while True:
        print("\nOptions:")
        print("1. Parse PDF file")
        print("2. Query document summary")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            pdf_path = input("Enter PDF file path: ").strip()
            if not pdf_path or not os.path.exists(pdf_path):
                print("File not found!")
                continue
            
            print("\nParsing PDF...")
            try:
                with open(pdf_path, "rb") as f:
                    files = {"file": (os.path.basename(pdf_path), f, "application/pdf")}
                    response = requests.post(f"{API_BASE_URL}/parse", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    print("\n✓ Parse successful!")
                    print(f"Document ID: {result['doc_id']}")
                    print(f"Equations: {result['summary']['equations_total']}")
                    print(f"Logic Formulas: {result['summary']['logic_total']}")
                    print(f"SRS Requirements: {result['summary']['srs_total']}")
                    print(f"Errors: {result['summary']['errors_total']}")
                else:
                    print(f"\n✗ Error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"\n✗ Error: {str(e)}")
        
        elif choice == "2":
            doc_id = input("Enter document ID: ").strip()
            if not doc_id:
                print("Document ID required!")
                continue
            
            print("\nFetching summary...")
            try:
                response = requests.get(f"{API_BASE_URL}/document/{doc_id}/summary")
                if response.status_code == 200:
                    summary = response.json()
                    print("\nSummary:")
                    print(json.dumps(summary, indent=2))
                else:
                    print(f"\n✗ Error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"\n✗ Error: {str(e)}")
        
        elif choice == "3":
            print("\nGoodbye!")
            break
        
        else:
            print("Invalid choice!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
