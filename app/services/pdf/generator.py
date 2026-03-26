import os
from fpdf import FPDF

class FinoraReceiptPDF(FPDF):
    def header(self):
        # Branding Header
        self.set_font("Arial", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(100, 10, "FINORA FINANCIAL SYSTEM", align="L")
        
        self.set_font("Arial", "I", 9)
        self.cell(0, 10, "Official Transaction Receipt", align="R", ln=True)
        
        # Indigo separator line (Matches your M3 theme)
        self.set_draw_color(79, 70, 229) 
        self.set_line_width(0.5)
        self.line(10, 18, 138, 18) # A5 width is 148mm
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(220, 220, 220)
        self.line(10, self.get_y(), 138, self.get_y())
        
        self.set_font("Arial", "I", 8)
        self.set_text_color(160, 160, 160)
        self.cell(70, 10, "© 2026 Finora App | HackSmiths", align="L")
        self.cell(0, 10, f"Page {self.page_no()}", align="R")

class ReceiptService:
    def __init__(self, export_dir):
        self.export_dir = export_dir
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir, exist_ok=True)

    def generate_receipt(self, record):
        """Generates a clean, modern PDF receipt for a single transaction."""
        # A5 is the industry standard for small receipts
        pdf = FinoraReceiptPDF(orientation='P', unit='mm', format='A5')
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # --- Title Section ---
        pdf.set_font("Arial", 'B', 20)
        pdf.set_text_color(31, 41, 55) # Deep Grey
        pdf.cell(0, 15, "Transaction Details", ln=True)
        
        # Meta info
        pdf.set_font("Arial", 'B', 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, f"RECEIPT ID: FIN-{record.id:05d}", ln=True)
        pdf.cell(0, 5, f"DATE: {record.transaction_date}", ln=True)
        pdf.ln(10)

        # --- Highlight Amount Box ---
        pdf.set_fill_color(249, 250, 251) # Very light grey
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(79, 70, 229) # Indigo
        amount_str = f"TOTAL AMOUNT: INR {record.amount:,.2f}"
        pdf.cell(0, 12, f"  {amount_str}", ln=True, fill=True)
        pdf.ln(5)

        # --- Details Table ---
        details = [
            ("Customer/Person:", record.person_name),
            ("Branch/Office:", record.branch_name),
            ("Type:", record.transaction_type),
            ("Payment Method:", record.transaction_method),
            ("Handled By:", record.received_by),
        ]

        pdf.set_text_color(50, 50, 50)
        for label, value in details:
            # Label
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(40, 9, label)
            # Value
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 9, str(value), ln=True)
            # Subtle dotted underline for each row
            pdf.set_draw_color(230, 230, 230)
            pdf.line(pdf.get_x(), pdf.get_y(), 138, pdf.get_y())

        # --- Final Polish: Status Stamp ---
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        if record.transaction_type == "Credit":
            pdf.set_text_color(34, 197, 94) # Green
            status = "FUNDS RECEIVED"
        else:
            pdf.set_text_color(239, 68, 68) # Red
            status = "FUNDS DISBURSED"
        
        pdf.cell(0, 10, f"STATUS: {status}", align='R', ln=True)

        # --- Save ---
        filename = f"Receipt_{record.person_name}_{record.id}.pdf".replace(" ", "_")
        full_path = os.path.join(self.export_dir, filename)
        pdf.output(full_path)
        
        return full_path