"""PDF generation and printing for bills."""
from __future__ import annotations

import os
import subprocess
from datetime import datetime
from typing import Iterable, Tuple

from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from billing_app.core.config import load_config
from billing_app.core.paths import resource_path
from billing_app.core.state import log_msg

BillRow = Tuple[int, str, str, float, float, str, float]


def _run_win_cmd(cmd: str) -> None:
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode not in (0, None):
        raise RuntimeError(f"Command failed: {cmd}\nstdout: {stdout}\nstderr: {stderr}")


class BillPrinter:
    def __init__(self, invoice_no: int, date_time: datetime, bill_items: Iterable[BillRow]):
        self.output_filename = "bill.pdf"
        self.invoice_no = invoice_no
        self.date_time = date_time
        self.bill_items = list(bill_items)
        config = load_config()
        self.invoice_prefix = str(config.get("invoice_prefix", "")) or ""

    def draw_bill(self, c: canvas.Canvas, x_offset: float, y_offset: float) -> None:
        _width, height = LETTER
        has_tax = any(item[6] != 0 for item in self.bill_items)

        c.drawImage(resource_path("header.png"), x_offset + 10, y_offset + 780, width=height / 2 - 40, height=50)
        y_position = y_offset + 760

        c.setFont("Helvetica", 10)
        c.drawString(x_offset + 20, y_position, f"Invoice No.: {self.invoice_prefix}{self.invoice_no:03d}")
        c.drawRightString(x_offset + 400, y_position, f"Date: {self.date_time.strftime('%d-%m-%y %H:%M')}")
        y_position -= 12

        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_offset + 20, y_position, "Item")
        c.drawString(x_offset + 80, y_position, "HSN")
        c.drawRightString(x_offset + 150, y_position, "Rate")
        c.drawString(x_offset + 160, y_position, "Quantity")
        c.drawString(x_offset + 200, y_position, "Unit")
        if has_tax:
            c.drawRightString(x_offset + 270, y_position, "Price")
            c.drawRightString(x_offset + 310, y_position, "GST %")
            c.drawRightString(x_offset + 360, y_position, "GST Amt.")
        c.drawRightString(x_offset + 400, y_position, "Amt.")
        y_position -= 6

        c.setFont("Helvetica", 8)
        total_amount = 0.0
        tax_amount = 0.0
        grand_total = 0.0
        for p_id, name, hsn, unit_price, quantity, unit, tax_perc in self.bill_items:
            price = unit_price * quantity
            if has_tax:
                unit_price_no_tax = unit_price * (100 / (tax_perc + 100)) if tax_perc else unit_price
                price_no_tax = unit_price_no_tax * quantity
                tax = price_no_tax * tax_perc / 100 if tax_perc else 0
                total_amount += price_no_tax
                tax_amount += tax
            grand_total += price

            name_style = ParagraphStyle(
                "NameStyle",
                fontName="Helvetica",
                fontSize=8,
                textColor=Color(0.3, 0.3, 0.3),
                leading=8,
            )
            p = Paragraph(name, name_style)
            p.wrapOn(c, 80, 20)
            y_position -= p.height
            p.drawOn(c, x_offset + 20, y_position)

            c.drawString(x_offset + 80, y_position, str(hsn))
            c.drawRightString(x_offset + 150, y_position, f"{unit_price:.2f}")
            c.drawString(x_offset + 160, y_position, str(quantity))
            c.drawString(x_offset + 200, y_position, unit)
            if has_tax:
                c.drawRightString(x_offset + 270, y_position, f"{price_no_tax:.2f}")
                c.drawRightString(x_offset + 310, y_position, f"{tax_perc:.2f}")
                c.drawRightString(x_offset + 360, y_position, f"{tax:.2f}")
            c.drawRightString(x_offset + 400, y_position, f"{price:.2f}")
            y_position -= 2

        y_position -= 2
        c.line(x_offset + 20, y_position, x_offset + 400, y_position)
        y_position -= 12
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_offset + 20, y_position, "Total:")
        if has_tax:
            c.drawRightString(x_offset + 270, y_position, f"{total_amount:.2f}")
            c.drawRightString(x_offset + 360, y_position, f"{tax_amount:.2f}")
        c.drawRightString(x_offset + 400, y_position, f"{grand_total:.2f}")

        y_position -= 20
        c.setFont("Helvetica-Bold", 8)
        if has_tax:
            half_tax = tax_amount / 2
            c.drawString(x_offset + 330 - stringWidth("CGST : Rs. ", "Helvetica-Bold", 8), y_position, f"CGST : Rs. {half_tax:.2f}")
            y_position -= 12
            c.drawString(x_offset + 330 - stringWidth("SGST : Rs. ", "Helvetica-Bold", 8), y_position, f"SGST : Rs. {half_tax:.2f}")
            y_position -= 12

        total_rounded = round(grand_total)
        c.drawString(
            x_offset + 330 - stringWidth("Round off: Rs. ", "Helvetica-Bold", 8),
            y_position,
            f"Round off: Rs. {(total_rounded - grand_total):.2f}",
        )
        y_position -= 12

        c.setFont("Helvetica-Bold", 10)
        c.drawString(
            x_offset + 330 - stringWidth("Grand Total: Rs. ", "Helvetica-Bold", 10),
            y_position,
            f"Grand Total: Rs. {total_rounded:.2f}",
        )

    def generate_bill_pdf(self) -> str:
        c = canvas.Canvas(self.output_filename, pagesize=A4)
        _width, height = A4
        color = Color(0.3, 0.3, 0.3)
        c.setFillColor(color)
        c.setStrokeColor(color)

        c.saveState()
        c.translate(height, 0)
        c.rotate(90)
        self.draw_bill(c, 0, 0)
        self.draw_bill(c, height / 2, 0)
        c.restoreState()
        c.line(0, height / 2, _width, height / 2)
        c.save()
        return self.output_filename

    def print_bill(self) -> None:
        self.generate_bill_pdf()
        gs_cmd = resource_path("bin\\gswin32c.exe")
        gsprint_cmd = resource_path("gsprint.exe")
        cmd = f"{gsprint_cmd} -ghostscript {gs_cmd} {self.output_filename}"
        try:
            _run_win_cmd(cmd)
        except Exception as exc:  # pylint: disable=broad-except
            log_msg(f"AutoPrint failed: {exc}")
            try:
                os.startfile(self.output_filename, "print")
            except Exception:  # pylint: disable=broad-except
                log_msg("Bill saved. Could not print bill")
                try:
                    os.startfile(self.output_filename)
                except Exception:  # pylint: disable=broad-except
                    log_msg("Could not open bill pdf. saved as bill.pdf")
