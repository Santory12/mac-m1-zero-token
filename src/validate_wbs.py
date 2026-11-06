#!/usr/bin/env python3
"""
WBS Gold Standard Validator for Innowise / Mikhail Labutin Presales.
Ensures strict syntactic, structural, and mathematical compliance.
"""

import sys
import csv
import re
from decimal import Decimal, InvalidOperation

EXPECTED_HEADERS = [
    "Business Requirement",
    "Work Breakdown Item (WBI)",
    "Phase",
    "Dev / Config",
    "Functional Areas / Odoo Features / Tasks",
    "Assumptions",
    "Risks",
    "Development Min",
    "Development Max",
    "Consultant Min",
    "Consultant Max"
]

MANDATORY_SECTIONS = [
    "DISCOVERY",
    "CONFIGURATION",
    "ROLES",
    "MIGRATION",
    "GO-LIVE",
    "HYPERCARE",
    "PROJECT MANAGEMENT"
]

def validate_wbs(filepath):
    errors = []
    warnings = []
    
    print(f"🔍 Validating WBS Gold Standard: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            sample = f.read(4096)
            if ';' not in sample:
                errors.append("Delimiter error: CSV must use semicolon ';' as delimiter.")
    except Exception as e:
        print(f"❌ Error opening file: {e}")
        return False

    rows = []
    with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.reader(f, delimiter=';')
        try:
            for line_no, row in enumerate(reader, start=1):
                rows.append((line_no, row))
        except Exception as e:
            errors.append(f"CSV Parse error at line {line_no}: {e}")

    if not rows:
        errors.append("File is empty.")
        report(errors, warnings)
        return False

    header_line, header = rows[0]
    cleaned_header = [h.strip().replace('"', '') for h in header]
    
    if len(cleaned_header) != 11:
        errors.append(f"Header column count error: Expected 11 columns, got {len(cleaned_header)}: {cleaned_header}")
    else:
        for idx, (exp, actual) in enumerate(zip(EXPECTED_HEADERS, cleaned_header)):
            if exp.lower() != actual.lower():
                errors.append(f"Header mismatch at col {idx+1}: Expected '{exp}', got '{actual}'")

    all_text = ""
    dev_min_total = 0
    dev_max_total = 0
    cons_min_total = 0
    cons_max_total = 0
    
    has_pm_buffer = False
    
    for line_no, row in rows[1:]:
        if not any(row):
            continue
            
        all_text += " ".join(row).upper() + " "
        
        if len(row) != 11:
            errors.append(f"Line {line_no}: Expected 11 columns, got {len(row)}. Row content: {row[:3]}...")
            continue
            
        req, wbi, phase, dev_conf, tasks, assumptions, risks, dev_min, dev_max, cons_min, cons_max = [c.strip() for c in row]
        
        if "PM" in wbi.upper() or "BUFFER" in wbi.upper() or "PROJECT MANAGEMENT" in req.upper() or "PROJECT MANAGEMENT" in phase.upper():
            has_pm_buffer = True

        # Check standard config dev hours
        if dev_conf.lower() in ["config", "configuration", "ootb"]:
            try:
                d_min = float(dev_min) if dev_min else 0
                d_max = float(dev_max) if dev_max else 0
                if d_min > 0 or d_max > 0:
                    warnings.append(f"Line {line_no} ('{wbi}'): OOTB Config task has Dev hours ({dev_min}-{dev_max}). Config should normally have Dev=0.")
            except ValueError:
                pass

        values = []
        for label, value in zip(EXPECTED_HEADERS[7:], [dev_min, dev_max, cons_min, cons_max]):
            try:
                number = Decimal(value) if value else Decimal(0)
                if not number.is_finite() or number < 0:
                    raise InvalidOperation
                values.append(number)
            except InvalidOperation:
                errors.append(f"Line {line_no}: invalid {label}: {value!r}")
                values.append(None)
        if all(v is not None for v in values):
            if values[0] > values[1] or values[2] > values[3]:
                errors.append(f"Line {line_no}: minimum exceeds maximum")
            if not any(kw in req.upper() for kw in ["TOTAL", "SUBTOTAL"]):
                dev_min_total += values[0]
                dev_max_total += values[1]
                cons_min_total += values[2]
                cons_max_total += values[3]

    # Check mandatory sections
    for sec in MANDATORY_SECTIONS:
        if sec not in all_text:
            warnings.append(f"Mandatory section/topic '{sec}' not explicitly detected in WBS.")

    # Check PM buffer
    if not has_pm_buffer:
        warnings.append("Project Management / 15% PM Buffer row was not detected.")

    print(f"📊 Calculated Hours (Line items):")
    print(f"   Dev: {dev_min_total} - {dev_max_total} hrs")
    print(f"   Consultant: {cons_min_total} - {cons_max_total} hrs")
    print(f"   Grand Total (pre-buffer): {dev_min_total + cons_min_total} - {dev_max_total + cons_max_total} hrs")
    print(f"   Recommended 15% PM Buffer: {round((dev_min_total + cons_min_total)*Decimal("0.15"))} - {round((dev_max_total + cons_max_total)*Decimal("0.15"))} hrs")

    return report(errors, warnings)

def report(errors, warnings):
    if warnings:
        print("\n⚠️  WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
            
    if errors:
        print("\n❌  ERRORS:")
        for e in errors:
            print(f"  - {e}")
        print("\n❌ WBS Validation FAILED.")
        return False
    else:
        print("\n✅ WBS Gold Standard Validation PASSED successfully!")
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 validate_wbs.py <path_to_wbs.csv>")
        sys.exit(1)
        
    success = validate_wbs(sys.argv[1])
    sys.exit(0 if success else 1)
