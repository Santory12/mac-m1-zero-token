#!/usr/bin/env python3
"""
checkodoo.py - Модуль 5 экосистемы mac-m1-zero-token.
Локальный линтер и валидатор Odoo 18/19 XML и Python артефактов.
Проверяет правила Innowise / Odoo Guidelines до отправки клиенту или тестирования в базе.
"""

import sys
import os
import re
import py_compile
import xml.etree.ElementTree as ET

def check_xml(file_path):
    print(f"🔍 Валидация Odoo XML: {file_path}")
    errors = []
    warnings = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return False

    # 1. Проверка синтаксиса XML
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        errors.append(f"Синтаксическая ошибка XML: {e}")
        print_results(errors, warnings)
        return False

    # Parse actual elements: comments and string literals are not XML nodes.
    if any(node.tag == "tree" for node in root.iter()):
        warnings.append("Found <tree>: review compatibility with the target Odoo version.")

    return print_results(errors, warnings)

def check_python(file_path):
    print(f"🔍 Валидация Odoo Python: {file_path}")
    errors = []
    warnings = []

    # 1. Компиляция Python байткода для проверки синтаксиса
    try:
        py_compile.compile(file_path, doraise=True)
    except py_compile.PyCompileError as e:
        errors.append(f"Ошибка синтаксиса Python: {e}")
        return print_results(errors, warnings)

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 2. Проверка импорта odoo models
    if "from odoo import" not in code and "import odoo" not in code:
        warnings.append("В файле нет явного импорта из библиотеки odoo (например: from odoo import models, fields, api).")

    # 3. Проверка классов моделей
    class_matches = re.findall(r"class\s+(\w+)\s*\((.*?)\):", code)
    for cls_name, base_classes in class_matches:
        if "Model" in base_classes or "TransientModel" in base_classes:
            # Проверяем наличие _name или _inherit
            cls_body_match = re.search(rf"class\s+{cls_name}.*?(?=\nclass|\Z)", code, re.DOTALL)
            if cls_body_match:
                cls_body = cls_body_match.group(0)
                if "_name" not in cls_body and "_inherit" not in cls_body:
                    errors.append(f"Класс модели {cls_name} не содержит атрибута _name или _inherit!")

    return print_results(errors, warnings)

def print_results(errors, warnings):
    if warnings:
        print(f"\n⚠️ Предупреждения ({len(warnings)}):")
        for w in warnings:
            print(f"  • {w}")

    if errors:
        print(f"\n❌ Найдено критических ошибок ({len(errors)}):")
        for e in errors:
            print(f"  • {e}")
        print("\nСтатус: FAILED")
        return False
    else:
        print("\n✅ Валидация успешно пройдена (0 ошибок). Статус: PASSED")
        return True

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Использование утилиты checkodoo (mac-m1-zero-token):")
        print("  checkodoo <файл.(xml|py)>")
        print("\nЛокально проверяет синтаксис и правила Odoo 18/19 до загрузки в базу данных.")
        sys.exit(0)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Ошибка: Файл не найден: {file_path}")
        sys.exit(1)

    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".xml":
        ok = check_xml(file_path)
    elif ext == ".py":
        ok = check_python(file_path)
    else:
        print(f"Предупреждение: Неизвестный формат файла '{ext}'. Поддерживаются только .xml и .py")
        sys.exit(1)

    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
