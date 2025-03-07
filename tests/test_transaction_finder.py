import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.transaction_finder import extract_transactions, group_similar_transactions, identify_recurring_transactions

def test_transaction_extraction():
    # Test data
    sample_lines = [
        "01/15/2024 Netflix #123 $19.99",
        "02/15/2024 NETFLIX SUBSCRIPTION $19.99",
        "01/20/2024 Amazon Prime*123 $14.99",
        "02/20/2024 Amazon Prime Mem $14.99",
        "03/20/2024 AMZN Prime $14.99",
        "01/25/2024 Grocery Store $52.47",  # Non-recurring transaction
    ]
    
    # Test extraction
    transactions = extract_transactions(sample_lines)
    assert len(transactions) == 6, f"Expected 6 transactions, got {len(transactions)}"
    print("✓ Transaction extraction test passed")
    
    # Test grouping
    grouped = group_similar_transactions(transactions)
    assert len(grouped) == 3, f"Expected 3 groups, got {len(grouped)}"
    assert "Netflix" in ' '.join(grouped.keys()), "Netflix group not found"
    assert "Amazon" in ' '.join(grouped.keys()), "Amazon group not found"
    print("✓ Transaction grouping test passed")
    
    # Test recurring identification
    recurring = identify_recurring_transactions(grouped)
    assert len(recurring) == 2, f"Expected 2 recurring merchants, got {len(recurring)}"
    assert "Grocery Store" not in recurring, "Non-recurring transaction incorrectly identified"
    print("✓ Recurring transaction identification test passed")
    
    # Print results
    print("\nTest Results:")
    print("\nRecurring Transactions Found:")
    for merchant, transactions in recurring.items():
        print(f"\n{merchant}:")
        for t in transactions:
            print(f"  {t}")

if __name__ == "__main__":
    print("Running transaction finder tests...")
    test_transaction_extraction() 