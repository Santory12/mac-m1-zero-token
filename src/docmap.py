#!/usr/bin/env python3
"""
docmap.py - Модуль 6 экосистемы mac-m1-zero-token.
Генерирует карту документа (оглавление) с точными номерами строк и оценкой токенов.
Позволяет ИИ-агентам адресно извлекать (read_file start_line/end_line) только
нужные разделы, не сжигая контекст на чтение всего файла.
"""

import sys
import os
import re

def estimate_tokens(text: str) -> int:
    words = len(text.split())
    chars = len(text)
    return max(words, chars // 3)

def generate_map(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        return f"❌ Ошибка чтения файла: {e}"

    total_lines = len(lines)
    full_text = "".join(lines)
    total_tokens = estimate_tokens(full_text)

    sections = []
    current_section = {"title": "Начало документа", "start": 1, "text": "", "level": 0}

    for i, line in enumerate(lines):
        line_num = i + 1
        # Ищем заголовки Markdown (H1-H6)
        match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
        if match:
            # Закрываем предыдущую секцию
            current_section["end"] = line_num - 1
            current_section["tokens"] = estimate_tokens(current_section["text"])
            if current_section["text"].strip() or current_section["title"] != "Начало документа":
                sections.append(current_section)
            
            # Начинаем новую секцию
            level = len(match.group(1))
            title = match.group(2).strip()
            current_section = {
                "title": f"{'  ' * (level - 1)}H{level}: {title}",
                "start": line_num,
                "text": line,
                "level": level
            }
        else:
            current_section["text"] += line

    # Закрываем последнюю секцию
    current_section["end"] = total_lines
    current_section["tokens"] = estimate_tokens(current_section["text"])
    sections.append(current_section)

    # Формируем отчет
    report = [
        f"🗺️  КАРТА ДОКУМЕНТА: {os.path.basename(file_path)}",
        f"📊 Всего строк: {total_lines} | Примерно токенов: ~{total_tokens:,}",
        "-" * 60,
        "Используйте эти координаты для точечного чтения (read_file start_line/end_line):",
        "-" * 60
    ]

    for sec in sections:
        # Пропускаем пустые начальные секции
        if sec["title"] == "Начало документа" and sec["tokens"] == 0:
            continue
        
        # Форматирование: [Строки 10-45] (~250 токенов) - H2: Название
        line_range = f"[{sec['start']:>4} - {sec['end']:>4}]"
        token_est = f"(~{sec['tokens']:>5} ток.)"
        
        # Ограничиваем длину заголовка для красоты вывода
        title = sec["title"]
        if len(title) > 60:
            title = title[:57] + "..."
            
        report.append(f"{line_range} {token_est} | {title}")

    report.append("-" * 60)
    report.append("💡 Подсказка Агенту: Вызывайте read_file с параметрами start_line и end_line,")
    report.append("чтобы извлечь конкретный раздел и не забивать окно контекста!")

    return "\n".join(report)

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Использование утилиты docmap (mac-m1-zero-token):")
        print("  docmap <файл.md|txt>")
        print("\nСоздает карту документа с точными номерами строк для адресного чтения.")
        sys.exit(0)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"❌ Ошибка: Файл не найден: {file_path}")
        sys.exit(1)

    print(generate_map(file_path))

if __name__ == "__main__":
    main()
