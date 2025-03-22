import sys
import os
import pytest
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.transaction import Transaction

def test_transaction_creation():
    """Test basic transaction creation with valid data."""
    transaction = Transaction(
        date=datetime(2024, 1, 1),
        merchant="Test Merchant",
        amount=99.99,
        credit_card="Test Card",
        description="Test Description"
    )
    
    assert transaction.date == datetime(2024, 1, 1)
    assert transaction.merchant == "Test Merchant"
    assert transaction.amount == 99.99
    assert transaction.credit_card == "Test Card"
    assert transaction.description == "Test Description"

def test_transaction_from_string():
    """Test creating transaction from string values."""
    transaction = Transaction.from_string(
        date_str="01/01/2024",
        merchant="Test Merchant",
        amount_str="$99.99",
        credit_card="Test Card",
        description="Test Description"
    )
    
    assert transaction.date == datetime(2024, 1, 1)
    assert transaction.merchant == "Test Merchant"
    assert transaction.amount == 99.99
    assert transaction.credit_card == "Test Card"
    assert transaction.description == "Test Description"

def test_transaction_amount_cleaning():
    """Test amount string cleaning with various formats."""
    test_cases = [
        ("$1,234.56", 1234.56),
        ("1234.56", 1234.56),
        ("$0.99", 0.99),
        ("1,000", 1000.0),
    ]
    
    for amount_str, expected in test_cases:
        transaction = Transaction.from_string(
            date_str="01/01/2024",
            merchant="Test",
            amount_str=amount_str,
            credit_card="Test Card"
        )
        assert transaction.amount == expected

def test_invalid_date_format():
    """Test error handling for invalid date format."""
    with pytest.raises(ValueError, match="Invalid date format"):
        Transaction.from_string(
            date_str="2024-01-01",  # Wrong format
            merchant="Test",
            amount_str="$99.99",
            credit_card="Test Card"
        )

def test_invalid_amount():
    """Test error handling for invalid amount format."""
    with pytest.raises(ValueError, match="Invalid amount format"):
        Transaction.from_string(
            date_str="01/01/2024",
            merchant="Test",
            amount_str="invalid",
            credit_card="Test Card"
        )

def test_string_representation():
    """Test the string representation of a transaction."""
    transaction = Transaction(
        date=datetime(2024, 1, 1),
        merchant="Test Merchant",
        amount=99.99,
        credit_card="Test Card",
        description="Test Description"
    )
    
    expected = "01/01/2024 | Test Merchant | $99.99 | Test Card - Test Description"
    assert str(transaction) == expected

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 