import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_parser import parse_pdf
from services.transaction_finder import extract_transactions, group_similar_transactions, identify_recurring_transactions

def analyze_pdf(pdf_path: str):
    """Analyze a single PDF and print results in a human-readable format."""
    print(f"\n{'='*80}")
    print(f"Analyzing PDF: {os.path.basename(pdf_path)}")
    print(f"{'='*80}")
    
    # Step 1: Extract text from PDF
    print("\n1. Extracting text from PDF...")
    lines = parse_pdf(pdf_path)
    print(f"Found {len(lines)} lines of text")
    
    # Print first few lines as sample
    print("\nSample of first 5 lines:")
    for line in lines[:5]:
        print(f"  {line}")
    
    # Step 2: Extract transactions
    print("\n2. Looking for transactions...")
    transactions = extract_transactions(lines)
    print(f"Found {len(transactions)} transactions")
    
    # Print first few transactions
    print("\nFirst 5 transactions found:")
    for t in transactions[:5]:
        print(f"  {t}")
    
    return transactions

def analyze_directory(directory_path: str):
    """Analyze all PDFs in a directory and identify recurring transactions."""
    print("\nAnalyzing all PDFs in directory...")
    
    # Collect all transactions from all PDFs
    all_transactions = []
    for filename in os.listdir(directory_path):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(directory_path, filename)
            transactions = analyze_pdf(file_path)
            all_transactions.extend(transactions)
    
    # Group similar transactions
    print(f"\n{'='*80}")
    print("Grouping similar transactions...")
    print(f"{'='*80}")
    grouped = group_similar_transactions(all_transactions)
    
    print("\nTransaction groups found:")
    for merchant, transactions in grouped.items():
        total = sum(t.amount for t in transactions)
        avg = total / len(transactions)
        print(f"\n{merchant}:")
        print(f"  Number of transactions: {len(transactions)}")
        print(f"  Total amount: ${total:.2f}")
        print(f"  Average amount: ${avg:.2f}")
        print("  Dates:")
        for t in sorted(transactions, key=lambda x: x.date):
            print(f"    {t.date.strftime('%m/%d/%Y')}: ${t.amount:.2f}")
    
    # Identify recurring transactions
    print(f"\n{'='*80}")
    print("Identifying recurring transactions...")
    print(f"{'='*80}")
    recurring = identify_recurring_transactions(grouped)
    
    print("\nRecurring transactions found:")
    total_monthly = 0
    for merchant, transactions in recurring.items():
        total = sum(t.amount for t in transactions)
        avg = total / len(transactions)
        total_monthly += avg
        print(f"\n{merchant}:")
        print(f"  Monthly cost: ${avg:.2f}")
        print("  Transaction history:")
        for t in sorted(transactions, key=lambda x: x.date):
            print(f"    {t.date.strftime('%m/%d/%Y')}: ${t.amount:.2f}")
    
    print(f"\nTotal potential monthly savings: ${total_monthly:.2f}")

if __name__ == "__main__":
    pdf_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "PDF")
    analyze_directory(pdf_dir) 