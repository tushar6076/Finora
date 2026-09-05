import os
from datetime import datetime
from xlsxwriter import Workbook

class ExcelGenerator:
    def __init__(self, export_dir):
        self.export_dir = export_dir
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir, exist_ok=True)

    def generate_report(self, records, filename_prefix="Finora_Report"):
        """
        Creates a high-quality XLSX file with validation and formatting.
        :param records: List of FinancialRecord objects from SQLAlchemy
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"{filename_prefix}_{timestamp}.xlsx"
        file_path = os.path.join(self.export_dir, filename)

        workbook = Workbook(file_path)
        worksheet = workbook.add_worksheet("Account Details")

        # --- Define Formats ---
        head_fmt = workbook.add_format({
            'bold': True, 'border': 1, 'align': 'center', 
            'valign': 'vcenter', 'font_name': 'Arial', 
            'font_size': 12, 'bg_color': '#4F46E5', 'font_color': 'white'
        })
        body_fmt = workbook.add_format({
            'border': 1, 'align': 'left', 'valign': 'vcenter', 
            'font_name': 'Calibri', 'font_size': 11
        })
        num_fmt = workbook.add_format({
            'border': 1, 'num_format': '₹#,##0.00', 'align': 'right'
        })

        # --- Headers ---
        headers = ["ID", "Person Name", "Branch Name", "Date", "Amount", "Type", "Method", "Handled By"]
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, head_fmt)

        # --- Data Validation ---
        num_rows = len(records) if records else 100 # Default to 100 rows for empty exports
        
        # Validation for Transaction Type (Dropdown)
        worksheet.data_validation(1, 5, num_rows, 5, {
            'validate': 'list',
            'source': ['Debit', 'Credit', 'Receipt'],
            'input_title': 'Transaction Type',
            'input_message': 'Select from list'
        })

        # Validation for Method (Dropdown)
        worksheet.data_validation(1, 6, num_rows, 6, {
            'validate': 'list',
            'source': ["Cash", "Check", "GPay", "Paytm", "PhonePe"],
            'input_title': 'Method',
            'input_message': 'Select payment way'
        })

        # --- Writing Data ---
        for row_num, record in enumerate(records, start=1):
            worksheet.write(row_num, 0, record.id, body_fmt)
            worksheet.write(row_num, 1, record.person_name, body_fmt)
            worksheet.write(row_num, 2, record.branch_name, body_fmt)
            worksheet.write(row_num, 3, record.transaction_date, body_fmt)
            worksheet.write(row_num, 4, record.amount, num_fmt)
            worksheet.write(row_num, 5, record.transaction_type, body_fmt)
            worksheet.write(row_num, 6, record.transaction_method, body_fmt)
            worksheet.write(row_num, 7, record.received_by, body_fmt)

        # --- Final Polish ---
        worksheet.set_column('A:A', 5)   # ID column
        worksheet.set_column('B:C', 25)  # Names
        worksheet.set_column('D:D', 15)  # Date
        worksheet.set_column('E:H', 20)  # Rest
        
        workbook.close()
        return file_path