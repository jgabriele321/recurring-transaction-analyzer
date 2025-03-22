import sys
import os
import pytest
from datetime import datetime
import tempfile
import csv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.csv_parser import CSVParser

def create_test_csv(filename, format_type, rows):
    """Helper function to create test CSV files."""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

@pytest.fixture
def temp_dir():
    """Fixture to create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

def test_amex_format_detection():
    """Test AMEX CSV format detection."""
    parser = CSVParser()
    header = ['Date', 'Description', 'Amount']
    assert parser._detect_format(header) == 'AMEX'

def test_chase_format_detection():
    """Test Chase CSV format detection."""
    parser = CSVParser()
    header = ['Status', 'Date', 'Description', 'Debit', 'Credit']
    assert parser._detect_format(header) == 'CHASE'

def test_invalid_format_detection():
    """Test invalid CSV format detection."""
    parser = CSVParser()
    header = ['Invalid', 'Headers']
    with pytest.raises(ValueError, match="Unsupported CSV format"):
        parser._detect_format(header)

def test_amex_transaction_parsing(temp_dir):
    """Test parsing AMEX format transactions."""
    test_data = [
        ['Date', 'Description', 'Amount'],
        ['01/15/2024', 'Netflix Subscription', '19.99'],
        ['01/16/2024', 'PAYMENT RECEIVED - THANK YOU', '-99.99'],  # Should be skipped
        ['01/17/2024', 'Amazon Prime', '14.99']
    ]
    
    test_file = os.path.join(temp_dir, 'Amex Test.csv')
    create_test_csv(test_file, 'AMEX', test_data)
    
    parser = CSVParser()
    transactions = parser.parse_csv(test_file)
    
    assert len(transactions) == 2  # Payment should be skipped
    assert transactions[0].merchant == 'Netflix Subscription'
    assert transactions[0].amount == 19.99
    assert transactions[0].credit_card == 'Amex Test'
    assert transactions[1].merchant == 'Amazon Prime'
    assert transactions[1].amount == 14.99

def test_chase_transaction_parsing(temp_dir):
    """Test parsing Chase format transactions."""
    test_data = [
        ['Status', 'Date', 'Description', 'Debit', 'Credit'],
        ['CLEARED', '01/15/2024', 'NETFLIX.COM', '19.99', ''],
        ['PENDING', '01/16/2024', 'AMAZON.COM', '29.99', ''],  # Should be skipped
        ['CLEARED', '01/17/2024', 'PAYMENT THANK YOU', '', '99.99'],  # Should be skipped
        ['CLEARED', '01/18/2024', 'Spotify Premium', '12.99', '']
    ]
    
    test_file = os.path.join(temp_dir, 'Chase Freedom.csv')
    create_test_csv(test_file, 'CHASE', test_data)
    
    parser = CSVParser()
    transactions = parser.parse_csv(test_file)
    
    assert len(transactions) == 2  # Pending and payment should be skipped
    assert transactions[0].merchant == 'NETFLIX.COM'
    assert transactions[0].amount == 19.99
    assert transactions[0].credit_card == 'Chase Freedom'
    assert transactions[1].merchant == 'Spotify Premium'
    assert transactions[1].amount == 12.99

def test_directory_parsing(temp_dir):
    """Test parsing multiple CSV files in a directory."""
    # Create AMEX test file
    amex_data = [
        ['Date', 'Description', 'Amount'],
        ['01/15/2024', 'Netflix', '19.99']
    ]
    amex_file = os.path.join(temp_dir, 'Amex.csv')
    create_test_csv(amex_file, 'AMEX', amex_data)
    
    # Create Chase test file
    chase_data = [
        ['Status', 'Date', 'Description', 'Debit', 'Credit'],
        ['CLEARED', '01/16/2024', 'Spotify', '12.99', '']
    ]
    chase_file = os.path.join(temp_dir, 'Chase.csv')
    create_test_csv(chase_file, 'CHASE', chase_data)
    
    parser = CSVParser()
    transactions = parser.parse_directory(temp_dir)
    
    assert len(transactions) == 2
    assert any(t.merchant == 'Netflix' and t.credit_card == 'Amex' for t in transactions)
    assert any(t.merchant == 'Spotify' and t.credit_card == 'Chase' for t in transactions)

def test_error_handling(temp_dir):
    """Test error handling for malformed CSV files."""
    # Create malformed CSV file
    bad_data = [
        ['Date', 'Description', 'Amount'],
        ['invalid_date', 'Test', 'not_a_number']
    ]
    bad_file = os.path.join(temp_dir, 'Bad.csv')
    create_test_csv(bad_file, 'AMEX', bad_data)
    
    parser = CSVParser()
    transactions = parser.parse_directory(temp_dir)
    assert len(transactions) == 0  # Should skip malformed transactions

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 