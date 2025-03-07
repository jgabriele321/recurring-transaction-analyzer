from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Transaction:
    """
    Represents a single transaction from a bank statement.
    """
    date: datetime
    merchant: str
    amount: float
    description: Optional[str] = None
    
    @classmethod
    def from_string(cls, date_str: str, merchant: str, amount_str: str, description: Optional[str] = None):
        """
        Create a Transaction from string values.
        
        Args:
            date_str (str): Date string in format MM/DD/YYYY
            merchant (str): Merchant name
            amount_str (str): Amount string (can include $ and commas)
            description (str, optional): Additional transaction description
            
        Returns:
            Transaction: New transaction instance
        """
        # Parse date
        try:
            date = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Expected MM/DD/YYYY")
        
        # Clean amount string and convert to float
        try:
            # Handle None or empty string
            if not amount_str:
                raise ValueError("Amount string cannot be empty")
                
            # Remove currency symbol, commas, and whitespace
            clean_amount = amount_str.replace("$", "").replace(",", "").strip()
            amount = float(clean_amount)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid amount format: {amount_str}. Error: {str(e)}")
        
        return cls(
            date=date,
            merchant=merchant.strip(),
            amount=amount,
            description=description.strip() if description else None
        )
    
    def __str__(self) -> str:
        """String representation of the transaction."""
        date_str = self.date.strftime("%m/%d/%Y")
        desc = f" - {self.description}" if self.description else ""
        return f"{date_str} | {self.merchant} | ${self.amount:.2f}{desc}" 