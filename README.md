# Recurring Transaction Analyzer

A Python application that helps you identify and manage recurring transactions from your credit card statements. The analyzer supports both CSV and PDF formats, with CSV being the recommended format for better accuracy and performance.

## Features

- Parse credit card statements (CSV recommended, PDF supported)
- Identify recurring transactions and subscriptions
- Calculate potential monthly savings
- Provide direct cancellation links for 100+ popular services
- Smart web search for unknown subscription services
- User-friendly GUI interface with sortable columns
- Support for multiple credit card formats (Amex, Chase, etc.)

## Why CSV?

We recommend using CSV files because they:
- Are more reliable to parse than PDFs
- Provide cleaner transaction data
- Process faster than PDFs
- Can be easily exported from most credit card websites
- Maintain consistent formatting

### How to Export CSV Statements

1. **American Express**:
   - Log in to your account at [americanexpress.com](https://www.americanexpress.com)
   - Go to "Statements & Activity"
   - Click "Download" and select "CSV"

2. **Chase**:
   - Log in to your account at [chase.com](https://www.chase.com)
   - Go to "Account Activity"
   - Click "Download" and select "CSV"

3. **Other Banks**:
   Most major credit card providers offer CSV downloads in their account activity or statements section.

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

1. Click "Browse" to select a folder containing your credit card statements (CSV recommended)
2. Click "Analyze" to process the statements
3. Review the recurring transactions and their estimated monthly costs
4. Use the provided cancellation links to manage your subscriptions
   - Direct links for 100+ popular services
   - Smart web search for unknown services
5. Sort results by clicking column headers
6. Remove transactions you want to keep by clicking the "❌" button

## Supported Credit Card Formats

### CSV Formats
- American Express (recommended)
- Chase (recommended)
- More formats coming soon...

### PDF Formats (Legacy Support)
- American Express
- Chase
- Note: PDF parsing is provided for legacy support but may be less reliable

## Privacy & Security

This application:
- Processes all files locally on your machine
- Does not send any financial data externally
- Only makes web requests to find cancellation links for unknown services
- Caches search results to minimize web requests
- Uses rate limiting for web searches to avoid being blocked

## Contributing

We welcome contributions! Areas we're looking to improve:
- Support for additional credit card CSV formats
- Enhanced subscription detection algorithms
- Additional merchant cancellation links
- UI/UX improvements

## Note

While we support both CSV and PDF files, we strongly recommend using CSV format for the best experience. PDF parsing can be unreliable due to varying formats and layouts across different statement types and time periods. 