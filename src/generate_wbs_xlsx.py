#!/usr/bin/env python3
"""
Automated 2-Tab XLSX Generator for Innowise Presale WBS Gold Standard.
Complies with Section 11 of Documents/GEMINI CLI Sandbox/Presale/GEMINI.md.
"""

import sys
import os
import csv
from decimal import Decimal, InvalidOperation
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def read_csv_rows(filepath):
    rows = []
    # UTF-8 with BOM or plain UTF-8
    with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.reader(f, delimiter=';')
        for r in reader:
            if any(cell.strip() for cell in r):
                rows.append([cell.strip() for cell in r])
    return rows

def numeric_value(value):
    if not value:
        return value
    try:
        number = Decimal(value)
        if not number.is_finite() or number < 0:
            raise ValueError(f"Invalid hours: {value!r}")
        return int(number) if number == number.to_integral_value() else float(number)
    except InvalidOperation:
        raise ValueError(f"Invalid hours: {value!r}")


def style_sheet(ws, rows, is_ru=False):
    # Palette
    HEADER_FILL = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid") # Dark slate
    HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    
    SECTION_FILL = PatternFill(start_color="E5E7EB", end_color="E5E7EB", fill_type="solid") # Light gray
    SECTION_FONT = Font(name="Calibri", size=11, bold=True, color="111827")
    
    TOTAL_FILL = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid") # Warm amber light
    TOTAL_FONT = Font(name="Calibri", size=11, bold=True, color="92400E")
    
    REGULAR_FONT = Font(name="Calibri", size=10, color="000000")
    
    THIN_BORDER = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )

    ALIGN_TEXT = Alignment(vertical="top", wrap_text=True)
    ALIGN_CENTER = Alignment(horizontal="center", vertical="top")
    ALIGN_HEADER = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for row_idx, r in enumerate(rows, start=1):
        if len(r) != 11:
            raise ValueError(f"Row {row_idx}: expected 11 columns, got {len(r)}")
        # Pad row to 11 columns
        padded_row = r + [""] * (11 - len(r))
        ws.append(padded_row)
        for column, value in enumerate(padded_row, 1):
            ws.cell(row_idx, column).data_type = "s"
        
        is_header = (row_idx == 1)
        first_cell_upper = padded_row[0].upper()
        
        # Section row detection: row has col 1 filled, cols 2-11 empty
        is_section = (not is_header and bool(padded_row[0]) and not any(padded_row[1:]))
        
        # Total row detection
        is_total = (not is_header and any(kw in first_cell_upper for kw in ["TOTAL", "ИТОГО", "ИТОГОВАЯ"]))
        
        for col_idx in range(1, 12):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = THIN_BORDER
            
            if is_header:
                cell.fill = HEADER_FILL
                cell.font = HEADER_FONT
                cell.alignment = ALIGN_HEADER
            elif is_section:
                cell.fill = SECTION_FILL
                cell.font = SECTION_FONT
                cell.alignment = ALIGN_TEXT
            elif is_total:
                cell.fill = TOTAL_FILL
                cell.font = TOTAL_FONT
                cell.alignment = ALIGN_CENTER if col_idx >= 8 else ALIGN_TEXT
                # Try convert numeric
                if col_idx >= 8:
                    cell.value = numeric_value(cell.value)
            else:
                cell.font = REGULAR_FONT
                # Cols 8,9,10,11 are numeric estimates
                if col_idx in [8, 9, 10, 11]:
                    cell.alignment = ALIGN_CENTER
                    cell.value = numeric_value(cell.value)
                else:
                    cell.alignment = ALIGN_TEXT

    # Set row dimensions
    ws.row_dimensions[1].height = 28
    
    # Freeze header
    ws.freeze_panes = "A2"
    
    # Enable autofilter
    ws.auto_filter.ref = f"A1:K{len(rows)}"
    
    # Approximate column widths
    col_widths = {
        1: 28, # Business Requirement
        2: 32, # WBI
        3: 14, # Phase
        4: 20, # Dev / Config
        5: 45, # Tasks
        6: 35, # Assumptions
        7: 35, # Risks
        8: 12, # Dev Min
        9: 12, # Dev Max
        10: 12, # Cons Min
        11: 12  # Cons Max
    }
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

def build_wbs_xlsx(en_csv_path, ru_csv_path, out_xlsx_path):
    if not os.path.isfile(en_csv_path):
        print(f"❌ EN CSV file not found: {en_csv_path}")
        return False
    if not os.path.isfile(ru_csv_path):
        print(f"❌ RU CSV file not found: {ru_csv_path}")
        return False

    en_rows = read_csv_rows(en_csv_path)
    ru_rows = read_csv_rows(ru_csv_path)

    if not en_rows or not ru_rows:
        raise ValueError("Both CSV files must contain a header")
    for rows in (en_rows, ru_rows):
        for row in rows[1:]:
            if len(row) != 11:
                raise ValueError("Expected 11 columns")
            vals = [numeric_value(v) or 0 for v in row[7:11]]
            if vals[0] > vals[1] or vals[2] > vals[3]:
                raise ValueError("Minimum exceeds maximum")
    wb = openpyxl.Workbook()
    # Sheet 1: English
    ws_en = wb.active
    ws_en.title = "English"
    style_sheet(ws_en, en_rows, is_ru=False)

    # Sheet 2: Русский
    ws_ru = wb.create_sheet(title="Русский")
    style_sheet(ws_ru, ru_rows, is_ru=True)

    wb.save(out_xlsx_path)
    print(f"✅ Successfully created 2-tab formatted XLSX: {out_xlsx_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 generate_wbs_xlsx.py <en_wbs.csv> <ru_wbs.csv> <output.xlsx>")
        sys.exit(1)
    success = build_wbs_xlsx(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.exit(0 if success else 1)
