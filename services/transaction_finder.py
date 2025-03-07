import re
from typing import List, Optional
import logging
from datetime import datetime
from thefuzz import fuzz
from models.transaction import Transaction

logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG level
logger = logging.getLogger(__name__)

def extract_transactions(lines: List[str]) -> List[Transaction]:
    """
    Extract transactions from text lines using pattern matching.
    Handles AmEx's multi-line transaction format.
    
    Args:
        lines (List[str]): Lines of text from a bank statement
        
    Returns:
        List[Transaction]: List of extracted transactions
    """
    transactions = []
    
    # Regular expressions for different transaction formats
    date_pattern = r'(\d{2}/\d{2}/\d{2})'
    amount_pattern = r'\$([0-9,]+\.\d{2})'
    foreign_amount_pattern = r'(\d+\.\d{2})\s+\$([0-9,]+\.\d{2})'
    
    skip_keywords = [
        'and/or Cash',
        'Advance',
        'Document Type',
        'Ticket Number',
        'From:',
        'To:',
        'Passenger Name',
        'MERCHANDISE',
        'RESTAURANT',
        'FAST FOOD',
        'GROCERY STORE'
    ]

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip lines with metadata
        if any(keyword in line for keyword in skip_keywords):
            i += 1
            continue
            
        # Try to match transaction patterns
        date_match = re.search(date_pattern, line)
        if date_match:
            try:
                # Extract date
                date_str = date_match.group(1)
                date = datetime.strptime(date_str, '%m/%d/%y')
                
                # Extract merchant name - everything between the date and amount
                # First try foreign currency format
                foreign_amount_match = re.search(foreign_amount_pattern, line)
                if foreign_amount_match:
                    # For foreign transactions, get everything between date and foreign amount
                    merchant = line[date_match.end():line.rfind(foreign_amount_match.group(1))].strip()
                    amount = float(foreign_amount_match.group(2).replace(',', ''))
                else:
                    # For USD transactions, get everything between date and USD amount
                    amount_match = re.search(amount_pattern, line)
                    if amount_match:
                        merchant = line[date_match.end():line.rfind('$')].strip()
                        amount = float(amount_match.group(1).replace(',', ''))
                    else:
                        i += 1
                        continue
                
                # Clean up merchant name
                merchant = re.sub(r'\s+', ' ', merchant)  # Replace multiple spaces with single space
                merchant = merchant.strip()
                
                # Skip if no merchant name found
                if not merchant:
                    i += 1
                    continue
                    
                logger.debug(f"Found transaction: Date={date}, Merchant={merchant}, Amount=${amount}")
                
                transaction = Transaction(
                    date=date,
                    merchant=merchant,
                    amount=amount
                )
                transactions.append(transaction)
                
            except Exception as e:
                logger.error(f"Error processing line: {line}")
                logger.error(f"Error details: {str(e)}")
                
        i += 1
    
    return transactions

def group_similar_transactions(transactions: List[Transaction], similarity_threshold: int = 70) -> dict[str, List[Transaction]]:
    """
    Group transactions with similar merchant names using fuzzy string matching.
    
    Args:
        transactions (List[Transaction]): List of transactions to group
        similarity_threshold (int): Threshold for fuzzy string matching (0-100)
        
    Returns:
        dict[str, List[Transaction]]: Dictionary mapping normalized merchant names to lists of transactions
    """
    groups: dict[str, List[Transaction]] = {}
    
    def normalize_merchant(name: str) -> str:
        """Normalize merchant name for comparison."""
        # Remove common suffixes and special characters
        name = re.sub(r'\s*(Inc\.|LLC|Ltd\.|Corp\.|#\d+|Subscription|Mem).*$', '', name, flags=re.IGNORECASE)
        # Remove location information
        name = re.sub(r'\s+(?:in|at)\s+.*$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+[A-Z]{2}(?:\s+|$)', ' ', name)  # Remove state codes
        # Convert to lowercase and remove non-alphanumeric characters
        name = ''.join(c.lower() for c in name if c.isalnum())
        # Common abbreviations
        name = name.replace('amzn', 'amazon')
        name = name.replace('aplpay', '')  # Remove Apple Pay prefix
        return name
    
    for transaction in transactions:
        normalized = normalize_merchant(transaction.merchant)
        matched = False
        logger.debug(f"Normalized merchant name: {transaction.merchant} -> {normalized}")
        
        # Try to find a matching group
        for existing_merchant in list(groups.keys()):  # Create a copy of keys to avoid runtime modification issues
            existing_normalized = normalize_merchant(existing_merchant)
            similarity = fuzz.ratio(normalized, existing_normalized)
            logger.debug(f"Comparing {normalized} with {existing_normalized}: {similarity}%")
            
            if similarity >= similarity_threshold:
                groups[existing_merchant].append(transaction)
                matched = True
                logger.debug(f"Matched {transaction.merchant} to existing group {existing_merchant}")
                break
        
        # If no match found, create a new group
        if not matched:
            groups[transaction.merchant] = [transaction]
            logger.debug(f"Created new group for {transaction.merchant}")
    
    return groups

def identify_recurring_transactions(grouped_transactions: dict[str, List[Transaction]], 
                                 min_occurrences: int = 2,
                                 max_days_between: int = 35,
                                 amount_variance_threshold: float = 0.10) -> dict[str, List[Transaction]]:
    """
    Identify subscription-like recurring transactions from grouped transactions.
    
    Args:
        grouped_transactions (dict[str, List[Transaction]]): Grouped transactions by merchant
        min_occurrences (int): Minimum number of occurrences to consider recurring
        max_days_between (int): Maximum number of days between transactions to consider them part of the same pattern
        amount_variance_threshold (float): Maximum allowed variance in transaction amounts (as a percentage)
        
    Returns:
        dict[str, List[Transaction]]: Dictionary of subscription-like recurring transactions
    """
    recurring = {}
    
    for merchant, transactions in grouped_transactions.items():
        if len(transactions) < min_occurrences:
            continue
            
        # Sort transactions by date
        sorted_transactions = sorted(transactions, key=lambda t: t.date)
        
        # Group transactions by similar amounts
        amount_groups = {}
        for trans in sorted_transactions:
            if trans.amount == 0:  # Skip zero-amount transactions
                continue
                
            matched = False
            for base_amount in amount_groups.keys():
                # Calculate percentage difference
                try:
                    diff = abs(trans.amount - base_amount) / base_amount
                    if diff <= amount_variance_threshold:
                        amount_groups[base_amount].append(trans)
                        matched = True
                        break
                except ZeroDivisionError:
                    continue
            if not matched:
                amount_groups[trans.amount] = [trans]
        
        # Find groups with regular intervals and consistent amounts
        for amount, similar_transactions in amount_groups.items():
            if len(similar_transactions) >= min_occurrences:
                # Check for regular intervals
                intervals = []
                for i in range(1, len(similar_transactions)):
                    days = (similar_transactions[i].date - similar_transactions[i-1].date).days
                    if days <= max_days_between:
                        intervals.append(days)
                
                # If we have consistent intervals and amounts, consider it a subscription
                if intervals and (
                    len(intervals) >= min_occurrences - 1  # At least min_occurrences-1 intervals
                    and max(intervals) <= max_days_between  # All intervals within range
                ):
                    try:
                        # Calculate average amount, skipping zero amounts
                        valid_amounts = [t.amount for t in similar_transactions if t.amount != 0]
                        if valid_amounts:  # Only proceed if we have valid amounts
                            avg_amount = sum(valid_amounts) / len(valid_amounts)
                            if merchant not in recurring:
                                recurring[merchant] = similar_transactions
                                logger.info(f"Identified subscription for {merchant} (${avg_amount:.2f}/period)")
                    except ZeroDivisionError:
                        logger.warning(f"Skipping {merchant} due to invalid amounts")
                        continue
                    
    return recurring

def find_recurring_transactions(transactions, similarity_threshold=0.85):
    # Group transactions by merchant similarity
    merchant_groups = {}
    
    for transaction in transactions:
        matched = False
        for merchant in merchant_groups:
            # Simple string similarity check
            if are_merchants_similar(merchant, transaction.merchant, similarity_threshold):
                merchant_groups[merchant].append(transaction)
                matched = True
                break
        
        if not matched:
            merchant_groups[transaction.merchant] = [transaction]
    
    # Filter for recurring transactions (at least 2 transactions)
    recurring = {
        merchant: transactions 
        for merchant, transactions in merchant_groups.items()
        if len(transactions) >= 2
    }
    
    return recurring

def are_merchants_similar(merchant1, merchant2, threshold=0.85):
    # Convert to lowercase and remove common variations
    def normalize(name):
        name = name.lower()
        name = re.sub(r'aplpay\s+', '', name)  # Remove AplPay prefix
        name = re.sub(r'\s+limited\b', '', name)  # Remove Limited suffix
        name = re.sub(r'\s+ltd\b', '', name)  # Remove Ltd suffix
        name = re.sub(r'\s+llc\b', '', name)  # Remove LLC suffix
        name = re.sub(r'\s+inc\b', '', name)  # Remove Inc suffix
        name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
        name = re.sub(r'\s+', '', name)  # Remove all whitespace
        return name
    
    norm1 = normalize(merchant1)
    norm2 = normalize(merchant2)
    
    # Calculate similarity ratio
    longer = max(len(norm1), len(norm2))
    if longer == 0:
        return False
        
    distance = sum(a != b for a, b in zip(norm1.ljust(longer), norm2.ljust(longer)))
    similarity = 1 - (distance / longer)
    
    return similarity >= threshold

if __name__ == "__main__":
    # Example usage
    sample_lines = [
        "01/16/25",
        "AplPay UNITED AIRLINES HOUSTON TX",
        "$2,694.51",
        "01/15/25",
        "Netflix Subscription",
        "$19.99",
        "12/15/24",
        "NETFLIX.COM CA",
        "$19.99",
    ]
    
    # Extract transactions
    transactions = extract_transactions(sample_lines)
    print("\nExtracted Transactions:")
    for t in transactions:
        print(t)
    
    # Group similar transactions
    grouped = group_similar_transactions(transactions)
    print("\nGrouped Transactions:")
    for merchant, group in grouped.items():
        print(f"\n{merchant}:")
        for t in group:
            print(f"  {t}")
    
    # Identify recurring transactions
    recurring = identify_recurring_transactions(grouped)
    print("\nRecurring Transactions:")
    for merchant, group in recurring.items():
        print(f"\n{merchant} (Monthly):")
        for t in group:
            print(f"  {t}") 