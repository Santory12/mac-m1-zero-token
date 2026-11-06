#!/usr/bin/env python3
"""
localsearch.py - Модуль 4 экосистемы mac-m1-zero-token.
Сверхбыстрый локальный поиск по базе пресейлов, архитектуре и памяти проектов
на базе ripgrep без расхода токенов в LLM.
"""

import sys
import os
import subprocess
import re

DEFAULT_SEARCH_PATHS = [
    os.path.expanduser("~/Documents/GEMINI CLI Sandbox/Presale"),
    os.path.expanduser("~/.gemini/tmp/mais/memory"),
    os.path.expanduser("~/Projects")
]

def print_help():
    print("Использование утилиты localsearch (mac-m1-zero-token):")
    print("  localsearch \"поисковый запрос\" [дополнительная_директория]")
    print("\nПримеры:")
    print("  localsearch \"KSeF\"                 -> Поиск по всем пресейлам и памяти")
    print("  localsearch \"NovaZone 3PL\"        -> Поиск интеграций NovaZone")
    print("  localsearch \"DATEV\" ~/Downloads   -> Поиск в конкретной папке")
    print("\nМгновенно находит релевантные куски с контекстом (0 токенов в облако).")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print_help()
        sys.exit(0)

    query = sys.argv[1]
    search_dirs = []

    if len(sys.argv) >= 3:
        custom_dir = os.path.expanduser(sys.argv[2])
        if os.path.exists(custom_dir):
            search_dirs.append(custom_dir)
        else:
            print(f"Предупреждение: Папка не найдена: {custom_dir}")

    # Добавляем стандартные пути, если они существуют
    for p in DEFAULT_SEARCH_PATHS:
        if os.path.exists(p) and p not in search_dirs:
            search_dirs.append(p)

    if not search_dirs:
        print("Ошибка: Нет доступных директорий для поиска.")
        sys.exit(1)

    print(f"🔍 Поиск «{query}» по локальной базе знаний...")

    # Формируем команду ripgrep
    # -i: case-insensitive
    # -C 2: 2 строки контекста вокруг совпадения
    # -M 300: макс. длина строки (отсекает минифицированные файлы)
    # -g: фильтр файлов (md, csv, py, xml, txt, docx)
    cmd = [
        "rg", "-i", "-C", "2", "-M", "300",
        "--heading", "--line-number",
        "-g", "!*.git*",
        "-g", "!*.pyc",
        "-g", "!__pycache__",
        "-g", "!*.iso",
        "-g", "!*.dsf",
        "-g", "!*.flac",
        "-g", "!*.mp3",
        query
    ] + search_dirs

    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        output = res.stdout.strip()
        if not output:
            print(f" Совпадений по запросу «{query}» не найдено.")
            sys.exit(0)

        # Подсчет совпадений
        matches_count = len(re.findall(rf"(?i){re.escape(query)}", output))
        print(f"✓ Найдено совпадений: {matches_count}\n")
        print("="*60)
        print(output)
        print("="*60)
        print("\n💡 Совет: Используйте найденные цитаты напрямую без загрузки целых файлов в Gemini/Codex.")
    except FileNotFoundError:
        print("Ошибка: ripgrep (rg) не найден. Установите его: brew install ripgrep")
        sys.exit(1)

if __name__ == "__main__":
    main()
