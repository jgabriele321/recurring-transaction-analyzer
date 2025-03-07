import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.transaction_finder import extract_transactions, find_recurring_transactions
from services.pdf_parser import parse_pdf
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_amex_transactions():
    # Get list of PDF files from sample_pdfs directory
    pdf_dir = os.path.join('data', 'sample_pdfs')
    logger.debug(f"Looking for PDFs in {pdf_dir}")
    
    if not os.path.exists(pdf_dir):
        logger.error(f"Directory {pdf_dir} does not exist!")
        return
        
    pdf_files = [
        f for f in os.listdir(pdf_dir) 
        if f.endswith('.pdf')
    ]
    
    logger.debug(f"Found PDF files: {pdf_files}")
    
    all_transactions = []
    
    # Process each PDF
    for pdf_file in pdf_files:
        logger.info(f"\nProcessing {pdf_file}...")
        
        # Parse PDF content
        pdf_path = os.path.join(pdf_dir, pdf_file)
        logger.debug(f"Reading PDF from {pdf_path}")
        content = parse_pdf(pdf_path)
        
        # Log first few lines of content for debugging
        logger.debug("First 10 lines of content:")
        for i, line in enumerate(content[:10]):
            logger.debug(f"Line {i}: {line}")
        
        # Extract transactions
        transactions = extract_transactions(content)
        logger.info(f"Found {len(transactions)} transactions")
        
        # Print first 5 transactions as sample
        if transactions:
            logger.info("\nSample transactions:")
            for t in transactions[:5]:
                logger.info(f"{t.date.strftime('%m/%d/%Y')} | {t.merchant} | ${t.amount:.2f}")
        else:
            logger.warning("No transactions found in this PDF!")
        
        all_transactions.extend(transactions)
    
    logger.info(f"\nTotal transactions found across all PDFs: {len(all_transactions)}")
    
    # Find recurring transactions
    recurring = find_recurring_transactions(all_transactions)
    
    # Print recurring transaction groups
    logger.info("\nRecurring Transaction Groups:")
    for merchant, transactions in recurring.items():
        total = sum(t.amount for t in transactions)
        avg = total / len(transactions)
        
        logger.info(f"\n{merchant}:")
        logger.info(f"Total amount: ${total:.2f}")
        logger.info(f"Average amount: ${avg:.2f}")
        logger.info("Transactions:")
        for t in sorted(transactions, key=lambda x: x.date):
            logger.info(f"  {t.date.strftime('%m/%d/%Y')}: ${t.amount:.2f}")

if __name__ == "__main__":
    test_amex_transactions() 