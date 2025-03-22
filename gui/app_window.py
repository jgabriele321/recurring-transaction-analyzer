import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import logging
from typing import Dict, List
import webbrowser
import threading

from services.csv_parser import CSVParser
from services.transaction_finder import group_similar_transactions, identify_recurring_transactions
from services.link_finder import LinkFinder
from models.transaction import Transaction

logger = logging.getLogger(__name__)

class AppWindow:
    def __init__(self, root: tk.Tk):
        """Initialize the main application window."""
        self.root = root
        self.root.title("Recurring Transaction Analyzer")
        self.root.geometry("1200x720")  # Increased from 1000x600 (20% larger)
        
        # Initialize services
        self.link_finder = LinkFinder()
        self.csv_parser = CSVParser()
        
        # Create the main layout
        self._create_widgets()
        
        # Store state
        self.recurring_transactions: Dict[str, List[Transaction]] = {}
        self.total_savings = 0.0
        self.sort_column = None
        self.sort_reverse = False
        
        # Store transaction amounts for updating total
        self.transaction_amounts = {}
    
    def _create_widgets(self):
        """Create and layout all GUI widgets."""
        # Top frame for input controls
        input_frame = ttk.Frame(self.root, padding="10 10 10 10")
        input_frame.pack(fill=tk.X, padx=10)
        
        # Folder selection
        ttk.Label(input_frame, text="CSV Statements Folder:").pack(side=tk.LEFT, padx=(0, 5))
        self.folder_path_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.folder_path_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Browse", command=self._browse_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Analyze", command=self._start_analysis).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.Frame(self.root, padding="10 5 10 5")
        status_frame.pack(fill=tk.X, padx=10)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(fill=tk.X)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            status_frame, 
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Results area
        results_frame = ttk.Frame(self.root, padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a treeview for recurring transactions
        columns = ("Remove", "Merchant", "Monthly Cost", "Credit Card", "Frequency", "Cancel Link")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        # Set column headings with sorting
        self.tree.heading("Remove", text="")
        self.tree.column("Remove", width=50, anchor="center")
        
        for col in columns[1:]:  # Skip the Remove column for sorting
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_column(c))
            width = 180 if col != "Cancel Link" else 240  # Increased column widths by 20%
            if col == "Frequency":
                width = 120  # Adjust width for frequency column
            self.tree.column(col, width=width)
        
        # Bind click events
        self.tree.bind('<Button-1>', self._on_click)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Total savings label
        self.savings_var = tk.StringVar(value="Potential Monthly Savings: $0.00")
        ttk.Label(self.root, textvariable=self.savings_var, padding="10").pack()
    
    def _update_status(self, message: str, progress: float = None):
        """Update status message and progress bar."""
        self.status_var.set(message)
        if progress is not None:
            self.progress_var.set(progress)
        self.root.update_idletasks()
    
    def _start_analysis(self):
        """Start analysis in a separate thread to keep GUI responsive."""
        folder = self.folder_path_var.get()
        if not folder:
            messagebox.showerror("Error", "Please select a folder containing CSV statements.")
            return
        
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Reset progress and status
        self.progress_var.set(0)
        self._update_status("Starting analysis...")
        
        # Start analysis in a separate thread
        thread = threading.Thread(target=self._analyze_statements)
        thread.daemon = True
        thread.start()
    
    def _analyze_statements(self):
        """Analyze CSV statements in the selected folder."""
        try:
            folder = self.folder_path_var.get()
            
            # Reset column headers
            for col in self.tree["columns"]:
                self.tree.heading(col, text=col)
            
            # Parse CSVs and extract transactions
            self._update_status("Reading CSV files...", 10)
            all_transactions = self.csv_parser.parse_directory(folder)
            
            if not all_transactions:
                self._update_status("No transactions found", 0)
                messagebox.showwarning("No Transactions", "No transactions found in the selected CSVs.")
                return
            
            # Group similar transactions
            self._update_status("Grouping similar transactions...", 40)
            grouped = group_similar_transactions(all_transactions)
            
            # Identify recurring transactions
            self._update_status("Identifying recurring transactions...", 70)
            self.recurring_transactions = identify_recurring_transactions(grouped)
            
            # Update the treeview
            self._update_status("Updating results...", 90)
            self.total_savings = 0.0
            
            for merchant, transactions in self.recurring_transactions.items():
                # Calculate monthly cost (average of transaction amounts)
                monthly_cost = sum(t.amount for t in transactions) / len(transactions)
                self.total_savings += monthly_cost
                
                # Get cancellation link
                cancel_link = self.link_finder.get_cancellation_link(merchant)
                
                # Get credit card (use the most recent transaction's card)
                recent_transaction = max(transactions, key=lambda t: t.date)
                credit_card = recent_transaction.credit_card
                
                # Add to treeview with X button
                self.tree.insert("", tk.END, values=(
                    "❌",  # Remove button
                    merchant,
                    f"${monthly_cost:.2f}",
                    credit_card,
                    f"{len(transactions)} times",
                    cancel_link or "N/A"
                ))
            
            # Update total savings
            self.savings_var.set(f"Potential Monthly Savings: ${self.total_savings:.2f}")
            self._update_status("Analysis complete!", 100)
            
        except Exception as e:
            logger.error(f"Error analyzing statements: {str(e)}")
            self._update_status(f"Error: {str(e)}", 0)
            messagebox.showerror("Error", f"Failed to analyze statements: {str(e)}")
    
    def _on_click(self, event):
        """Handle click events on the treeview."""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item = self.tree.identify_row(event.y)
            
            if column == "#1":  # Remove column
                self._remove_item(item)
            elif column == "#6":  # Cancel Link column
                link = self.tree.item(item)['values'][5]
                if link and link != "N/A":
                    webbrowser.open(link)
    
    def _remove_item(self, item):
        """Remove an item from the treeview and update total savings."""
        values = self.tree.item(item)['values']
        amount = float(values[2].replace('$', '').replace(',', ''))
        self.total_savings -= amount
        self.savings_var.set(f"Potential Monthly Savings: ${self.total_savings:.2f}")
        self.tree.delete(item)
    
    def _sort_column(self, column):
        """Sort tree contents when a column header is clicked."""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
            self.sort_column = column
        
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children("")]
        
        # Convert amounts to float for proper numeric sorting
        if column == "Monthly Cost":
            items = [(float(amount.replace("$", "").replace(",", "")), item) for amount, item in items]
        elif column == "Frequency":
            # Extract the number from "X times" format for sorting
            items = [(int(freq.split()[0]), item) for freq, item in items]
        
        # Sort the items
        items.sort(reverse=self.sort_reverse)
        
        # Rearrange items in sorted positions
        for index, (val, item) in enumerate(items):
            self.tree.move(item, "", index)
        
        # Update sort indicator
        self.tree.heading(column, text=column + (" ↑" if self.sort_reverse else " ↓"))
    
    def _browse_folder(self):
        """Open a folder selection dialog."""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path_var.set(folder)

def run_app():
    """Create and run the application."""
    root = tk.Tk()
    app = AppWindow(root)
    root.mainloop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_app() 