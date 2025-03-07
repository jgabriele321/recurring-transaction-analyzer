import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_parser import parse_pdf

def examine_pdf_content(pdf_path: str):
    """Examine the raw content of a PDF file."""
    print(f"\n{'='*80}")
    print(f"Examining PDF: {os.path.basename(pdf_path)}")
    print(f"{'='*80}")
    
    # Extract text from PDF
    lines = parse_pdf(pdf_path)
    
    print(f"\nTotal lines found: {len(lines)}")
    
    # Look for potential transaction patterns
    print("\nPotential transaction patterns found:")
    print("-" * 80)
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for date-like patterns
        if any(c.isdigit() for c in line):
            # Print the current line and next few lines for context
            print(f"\nLine {i+1}:")
            print(f"  {line}")
            for j in range(1, 4):  # Print next 3 lines
                if i + j < len(lines):
                    print(f"Line {i+j+1}:")
                    print(f"  {lines[i+j].strip()}")
        i += 1
    
    print("\nFull content:")
    print("-" * 80)
    for i, line in enumerate(lines, 1):
        print(f"{i:3d}: {line}")

if __name__ == "__main__":
    pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "PDF")
    
    # Examine first PDF only to avoid too much output
    for filename in os.listdir(pdf_dir):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(pdf_dir, filename)
            examine_pdf_content(file_path)
            break  # Only examine first PDF 