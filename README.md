# Recurring Transaction Analyzer

A Python application that helps you identify and manage recurring transactions from your bank statements.

## Features

- Parse PDF bank statements
- Identify recurring transactions
- Calculate potential monthly savings
- Provide cancellation links for subscriptions
- User-friendly GUI interface

## Setup

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Usage

1. Click "Browse" to select a folder containing your PDF bank statements
2. Click "Analyze" to process the statements
3. Review the recurring transactions and their estimated monthly costs
4. Use the provided cancellation links to manage your subscriptions

## Note

This application processes PDF files locally on your machine and does not send any data externally. 