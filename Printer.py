import os
import tempfile
import platform
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.colors import Color
from reportlab.platypus import Paragraph
from GlobalAccess import resource_path, LogMsg
from datetime import datetime

import subprocess
def run_win_cmd(cmd):
    result = []
    process = subprocess.Popen(cmd,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    for line in process.stdout:
        result.append(line)
    errcode = process.returncode
    # for line in result:
    #     print(line)
    if errcode is not None:
        raise Exception('cmd %s failed, see above for details', cmd)
    
class BillPrinter:
    def __init__(self, invoice_no, date_time, bill_items):
        self.output_filename = "bill.pdf"
        self.invoice_no = invoice_no
        self.date_time = date_time
        self.bill_items = bill_items
    
    def draw_bill(self, c : canvas.Canvas, x_offset, y_offset):
        width, height = LETTER
        
        # # Add heading
        # c.setFont("Helvetica-Bold", 16)
        # c.drawString(x_offset + 20, y_offset + height - 20, "J&J Associates")
        
        # # Add Bill Receipt title
        # c.setFont("Helvetica", 12)
        # c.drawString(x_offset + 20, y_offset + height - 40, "Bill Receipt")
        
        # Add Bill Receipt title image
        c.drawImage(resource_path("header.png"), x_offset+10, y_offset+780, width=height/2-40, height=50)
        y_position = y_offset + 760

        # Add Invoice No. and Date
        c.setFont("Helvetica", 10)
        c.drawString(x_offset + 20, y_position, f"Invoice No.: A{self.invoice_no:03d}")
        c.drawRightString(x_offset + 400, y_position, f"Date: {self.date_time.strftime("%d-%m-%y %H:%M")}")
        y_position -= 12

        # table headings
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_offset + 20, y_position, "Item")
        c.drawString(x_offset + 80, y_position, "HSN")
        c.drawRightString(x_offset + 150, y_position, "Rate")
        c.drawString(x_offset + 160, y_position, "Quantity")
        c.drawString(x_offset + 200, y_position, "Unit")
        c.drawRightString(x_offset + 270, y_position, "Price")
        c.drawRightString(x_offset + 310, y_position, "GST %")
        c.drawRightString(x_offset + 360, y_position, "GST Amt.")
        c.drawRightString(x_offset + 400, y_position, "Amt.")
        y_position -= 6

        # items
        c.setFont("Helvetica", 8)
        total_amount = 0
        tax_amount = 0
        grand_total = 0
        for id, name, HSN, unit_price, quantity, unit, tax_perc in self.bill_items:
            unit_price_no_tax = unit_price * (100 / (tax_perc + 100))
            price_no_tax = unit_price_no_tax * quantity
            tax = price_no_tax * tax_perc / 100
            price = unit_price * quantity

            total_amount += price_no_tax
            tax_amount += tax
            grand_total += price
            
            # Wrap text for name
            # wrapped_name = textwrap.wrap(name, wrap_width)
            # name_lines = len(wrapped_name)
            name_style = ParagraphStyle(
                'NameStyle',
                fontName='Helvetica',
                fontSize=8,
                textColor=Color(0.3, 0.3, 0.3),
                leading=8  # Adjust line spacing if needed
            )
            p = Paragraph(name, name_style)
            p.wrapOn(c, 80, 20)
            y_position -= p.height
            p.drawOn(c, x_offset+20, y_position)

            # for i, line in enumerate(wrapped_name):
            #     c.drawString(x_offset + 20, y_position - (i * 12), line)

            c.drawString(x_offset + 80, y_position, str(HSN))
            c.drawRightString(x_offset + 150, y_position, f"{unit_price_no_tax:.2f}")
            c.drawString(x_offset + 160, y_position, str(quantity))
            c.drawString(x_offset + 200, y_position, unit)
            c.drawRightString(x_offset + 270, y_position, f"{price_no_tax:.2f}")
            c.drawRightString(x_offset + 310, y_position, f"{tax_perc:.2f}")
            c.drawRightString(x_offset + 360, y_position, f"{tax:.2f}")
            c.drawRightString(x_offset + 400, y_position, f"{price:.2f}")
            y_position -= 2
        
        y_position -= 2
        
        c.line(x_offset + 20, y_position, x_offset + 400, y_position)
        # totals
        y_position -= 12
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_offset + 20, y_position, "Total:")
        c.drawRightString(x_offset + 270, y_position, f"{total_amount:.2f}")
        c.drawRightString(x_offset + 360, y_position, f"{tax_amount:.2f}")
        c.drawRightString(x_offset + 400, y_position, f"{grand_total:.2f}")

        y_position -= 20

        c.setFont("Helvetica-Bold", 8)
        half_tax = tax_amount / 2
        prefix = "CGST : Rs. "
        c.drawString(x_offset + 330 - stringWidth(prefix, "Helvetica-Bold", 8), y_position, prefix + f"{half_tax:.2f}")
        y_position -= 12

        prefix = "SGST : Rs. "
        c.drawString(x_offset + 330 - stringWidth(prefix, "Helvetica-Bold", 8), y_position, prefix + f"{half_tax:.2f}")
        y_position -= 12

        total_rounded = round(grand_total)
        prefix = "Round off: Rs. "
        c.drawString(x_offset + 330 - stringWidth(prefix, "Helvetica-Bold", 8), y_position, prefix + f"{(total_rounded - grand_total):.2f}")
        y_position -= 12

        c.setFont("Helvetica-Bold", 10)
        prefix = "Grand Total: Rs. "
        c.drawString(x_offset + 330 - stringWidth(prefix, "Helvetica-Bold", 10), y_position, prefix + f"{total_rounded:.2f}")
    
    def generate_bill_pdf(self):
        c = canvas.Canvas(self.output_filename, pagesize=A4)
        width, height = A4
        # print(width, height)
        # create color from rgb
        # RGB values for the color
        r, g, b = 0.3, 0.3, 0.3
        color = Color(r, g, b)
        c.setFillColor(color)
        c.setStrokeColor(color)

        # Draw two copies of the bill on the same page, splitting the page in half horizontally
        c.saveState()  # Save current state
        c.translate(height, 0)  # Move to (x, y) position
        c.rotate(90)  # Rotate counterclockwise
        self.draw_bill(c, 0, 0)
        self.draw_bill(c, height/2, 0)
        c.restoreState() 

        c.line(0, height/2, width, height/2)
        
        c.save()
        return self.output_filename
    
    def print_bill(self):
        # with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        #     pdf_filename = temp_pdf.name
        
        self.generate_bill_pdf()
        print(resource_path("bin\\gswin32c.exe"))

        cmd = resource_path("gsprint.exe") + " -ghostscript "+ resource_path("bin\\gswin32c.exe") +" bill.pdf"
        try:
            run_win_cmd(cmd)
            pass
        except:
            LogMsg("AutoPrint Failed")
            try:
                os.startfile('bill.pdf', "print")
            except:
                LogMsg("Bill saved. Could not print bill")
                try:
                    os.startfile('bill.pdf')
                except:
                    LogMsg("Could not open bill pdf. saved as bill.pdf")
            

        # import win32print, win32api
        # GHOSTSCRIPT_PATH = resource_path("bin/gswin32.exe")
        # GSPRINT_PATH = resource_path("gsprint.exe")

        # # YOU CAN PUT HERE THE NAME OF YOUR SPECIFIC PRINTER INSTEAD OF DEFAULT
        # try:
        #     currentprinter = win32print.GetDefaultPrinter()
        #     print(GHOSTSCRIPT_PATH, GSPRINT_PATH, currentprinter)

        #     cmd = f'"{GHOSTSCRIPT_PATH}" -dPrinted -dBATCH -dNOPAUSE -dFitPage -sDEVICE=mswinpr2 -sOutputFile="%printer%{currentprinter}" "bill.pdf"'
        #     win32api.ShellExecute(0, 'open', 'cmd.exe', f'/c {cmd}', '.', 0)

        #     # win32api.ShellExecute(0, 'open', GSPRINT_PATH, '-ghostscript "'+GHOSTSCRIPT_PATH+'" -color -printer "'+currentprinter+'" -fit "bill.pdf"', '.', 0)
        # except:
        #     LogMsg("Bill saved. Could not print bill")
        
        # os.remove(pdf_filename)

# Example Usage
if __name__ == "__main__":
    # bill_data = {
    #     "Item A": {"unit_price": 10.99, "quantity": 2},
    #     "Item B": {"unit_price": 5.49, "quantity": 3},
    #     "Item C": {"unit_price": 3.75, "quantity": 1}
    # }
    from database import DataBase
    db = DataBase('database/sql.db')
    bill = db.getCurrentBill()

    printer = BillPrinter(db.getNextBillId(), db.get_curr_date(), bill)

    pdf_file = printer.generate_bill_pdf()
    # print(f"Bill PDF created: {pdf_file}")
    # print(BillPrinter().printer_name)