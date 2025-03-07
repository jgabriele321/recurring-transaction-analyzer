import pdfplumber
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_pdf(file_path: str) -> List[str]:
    """
    Parse a PDF file and extract text from each page, including tables.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        List[str]: List of text lines from the PDF
    """
    lines = []
    try:
        with pdfplumber.open(file_path) as pdf:
            logger.info(f"Processing PDF: {file_path}")
            for page_num, page in enumerate(pdf.pages, 1):
                logger.debug(f"Processing page {page_num}")
                
                # First try to extract tables
                tables = page.extract_tables()
                if tables:
                    logger.debug(f"Found {len(tables)} tables on page {page_num}")
                    for table in tables:
                        for row in table:
                            # Convert all cells to strings and filter out None/empty cells
                            row_text = ' '.join(str(cell).strip() for cell in row if cell is not None and str(cell).strip())
                            if row_text:
                                lines.append(row_text)
                                logger.debug(f"Table row: {row_text}")
                
                # Then extract regular text
                text = page.extract_text()
                if text:
                    logger.debug(f"Extracted text from page {page_num}")
                    # Split text into lines and filter out empty lines
                    page_lines = [line.strip() for line in text.split('\n') if line.strip()]
                    lines.extend(page_lines)
                else:
                    # If regular text extraction fails, try extracting words directly
                    words = page.extract_words()
                    if words:
                        logger.debug(f"Extracted {len(words)} words from page {page_num}")
                        current_line = []
                        current_y = None
                        
                        for word in words:
                            # If this is a new line (based on y-position)
                            if current_y is None or abs(word['top'] - current_y) > 3:  # 3 pixels tolerance
                                if current_line:
                                    lines.append(' '.join(current_line))
                                current_line = [word['text']]
                                current_y = word['top']
                            else:
                                current_line.append(word['text'])
                        
                        # Don't forget the last line
                        if current_line:
                            lines.append(' '.join(current_line))
                    else:
                        logger.warning(f"No content extracted from page {page_num}")
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {str(e)}")
        raise
    
    # Remove duplicate lines and sort by any date-like patterns
    unique_lines = list(dict.fromkeys(lines))
    return unique_lines

def parse_pdf_directory(directory_path: str) -> dict[str, List[str]]:
    """
    Parse all PDF files in a directory.
    
    Args:
        directory_path (str): Path to directory containing PDF files
        
    Returns:
        dict[str, List[str]]: Dictionary mapping filenames to their extracted lines
    """
    import os
    
    results = {}
    for filename in os.listdir(directory_path):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(directory_path, filename)
            try:
                results[filename] = parse_pdf(file_path)
            except Exception as e:
                logger.error(f"Failed to process {filename}: {str(e)}")
                results[filename] = []
    
    return results

if __name__ == "__main__":
    # Example usage and testing
    import sys
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        lines = parse_pdf(test_file)
        print(f"Extracted {len(lines)} lines from {test_file}")
        print("\nFirst 10 lines:")
        for line in lines[:10]:
            print(line) 