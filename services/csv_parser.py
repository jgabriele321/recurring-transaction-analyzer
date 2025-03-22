import csv
from typing import List, Optional
import logging
from datetime import datetime
import os
from models.transaction import Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVParser:
    """Parser for credit card statement CSV files."""
    
    def __init__(self):
        self.supported_formats = {
            'AMEX': self._parse_amex_row,
            'CHASE': self._parse_chase_row
        }
    
    def _detect_format(self, header: List[str]) -> str:
        """Detect the CSV format based on the header row."""
        header_str = ','.join(header).lower()
        
        if 'status' in header_str and 'debit' in header_str and 'credit' in header_str:
            return 'CHASE'
        elif len(header) == 3 and 'date' in header_str and 'description' in header_str and 'amount' in header_str:
            return 'AMEX'
        else:
            raise ValueError(f"Unsupported CSV format. Header: {header}")
    
    def _parse_amex_row(self, row: dict, credit_card: str) -> Optional[Transaction]:
        """Parse a row from an Amex CSV file."""
        try:
            # Skip certain transaction types
            if any(skip in row['Description'].upper() for skip in [
                'PAYMENT RECEIVED', 'INTEREST CHARGE', 'ANNUAL FEE'
            ]):
                return None
                
            date = datetime.strptime(row['Date'], '%m/%d/%Y')
            amount = float(row['Amount'])
            
            return Transaction(
                date=date,
                merchant=row['Description'].strip(),
                amount=abs(amount),  # Use absolute value since Amex uses positive for charges
                credit_card=credit_card
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to parse Amex row: {row}. Error: {str(e)}")
            return None
    
    def _parse_chase_row(self, row: dict, credit_card: str) -> Optional[Transaction]:
        """Parse a row from a Chase CSV file."""
        try:
            # Skip payments and pending transactions
            if (row['Status'].upper() != 'CLEARED' or
                'PAYMENT' in row['Description'].upper()):
                return None
                
            date = datetime.strptime(row['Date'], '%m/%d/%Y')
            
            # Chase uses separate debit/credit columns
            amount = float(row['Debit'] or '0') or -float(row['Credit'] or '0')
            
            # Clean up description (remove card numbers and null values)
            description = row['Description'].strip('"')
            description = description.split(' null ')[0]
            description = description.split(' XXXXXXXXXXXX')[0]
            
            return Transaction(
                date=date,
                merchant=description.strip(),
                amount=abs(amount),  # Use absolute value for consistency
                credit_card=credit_card
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to parse Chase row: {row}. Error: {str(e)}")
            return None
    
    def parse_csv(self, file_path: str) -> List[Transaction]:
        """
        Parse a CSV file and extract transactions.
        
        Args:
            file_path (str): Path to the CSV file
            
        Returns:
            List[Transaction]: List of extracted transactions
        """
        transactions = []
        
        # Extract credit card name from filename
        credit_card = os.path.splitext(os.path.basename(file_path))[0]
        
        try:
            with open(file_path, 'r') as f:
                # Read the header to detect format
                reader = csv.DictReader(f)
                csv_format = self._detect_format(reader.fieldnames)
                parse_row = self.supported_formats[csv_format]
                
                logger.info(f"Detected {csv_format} format for {file_path}")
                
                # Parse each row
                for row in reader:
                    transaction = parse_row(row, credit_card)
                    if transaction:
                        transactions.append(transaction)
                        
        except Exception as e:
            logger.error(f"Error processing CSV {file_path}: {str(e)}")
            raise
        
        return transactions
    
    def parse_directory(self, directory_path: str) -> List[Transaction]:
        """
        Parse all CSV files in a directory.
        
        Args:
            directory_path (str): Path to directory containing CSV files
            
        Returns:
            List[Transaction]: Combined list of transactions from all files
        """
        all_transactions = []
        
        for filename in os.listdir(directory_path):
            if filename.lower().endswith(('.csv', '.CSV')):
                file_path = os.path.join(directory_path, filename)
                try:
                    transactions = self.parse_csv(file_path)
                    logger.info(f"Extracted {len(transactions)} transactions from {filename}")
                    all_transactions.extend(transactions)
                except Exception as e:
                    logger.error(f"Failed to process {filename}: {str(e)}")
        
        return all_transactions

if __name__ == "__main__":
    # Example usage
    parser = CSVParser()
    sample_dir = "data/Sample CSV"
    
    if os.path.exists(sample_dir):
        transactions = parser.parse_directory(sample_dir)
        print(f"\nExtracted {len(transactions)} total transactions")
        print("\nSample transactions:")
        for t in transactions[:5]:
            print(f"{t}") 